from __future__ import annotations

from datetime import date
from uuid import uuid4

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models import PeriodoLetivoRecord, PrazoEtapaRecord, TCCRecord, UserRecord
from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import StatusTCC
from backend.app.models.user import Perfil
from backend.app.schemas.periodo import (
    CronogramaAlunoResponse,
    CronogramaOrientandoResponse,
    CronogramaPeriodoResponse,
    CronogramaPrazoResponse,
    CreatePeriodoRequest,
    PeriodoResumoResponse,
    PeriodoResponse,
    PeriodoWriteRequest,
    PrazoPayload,
    PrazoResponse,
    UpdatePeriodoRequest,
)
from backend.app.services.audit_service import AuditService

ACTIVE_PERIOD_CONFLICT_DETAIL = "Ja existe um periodo letivo ativo."
INACTIVE_PERIOD_EDIT_DETAIL = "Apenas periodos ativos podem ser editados."
OVERLAPPING_PERIOD_CONFLICT_DETAIL = "Ja existe um periodo letivo configurado para o intervalo informado."
PERIODO_NOT_FOUND_DETAIL = "Periodo letivo nao encontrado."
NO_ACTIVE_PERIODO_FOUND_DETAIL = "Nenhum periodo letivo ativo encontrado."
PERIODO_SAVE_CONFLICT_DETAIL = "Nao foi possivel salvar o periodo letivo informado."
CRONOGRAMA_FORBIDDEN_DETAIL = "Perfil sem permissao para visualizar o cronograma."
ORIENTANDO_NOT_FOUND_DETAIL = "Orientando nao encontrado para este professor."


class PeriodoService:
    def create_periodo(
        self,
        *,
        session: Session,
        payload: CreatePeriodoRequest,
    ) -> PeriodoResponse:
        self._ensure_no_date_overlap(
            session=session,
            data_inicio=payload.data_inicio,
            data_fim=payload.data_fim,
        )
        if payload.ativo:
            self._ensure_single_active_period(session=session)

        periodo = PeriodoLetivoRecord(
            id=str(uuid4()),
            nome=payload.nome,
            data_inicio=payload.data_inicio,
            data_fim=payload.data_fim,
            ativo=payload.ativo,
            prazos=self._build_prazos(payload.prazos),
        )

        self._persist_periodo(
            session=session,
            periodo=periodo,
            active_requested=payload.ativo,
            data_inicio=payload.data_inicio,
            data_fim=payload.data_fim,
        )
        return self.get_periodo_by_id(session=session, periodo_id=periodo.id)

    def list_periodos(self, *, session: Session) -> list[PeriodoResponse]:
        periodos = session.scalars(
            select(PeriodoLetivoRecord)
            .options(selectinload(PeriodoLetivoRecord.prazos))
            .order_by(PeriodoLetivoRecord.data_inicio.desc(), PeriodoLetivoRecord.nome.asc())
        ).all()
        return [self._build_periodo_response(periodo) for periodo in periodos]

    def get_periodo_by_id(self, *, session: Session, periodo_id: str) -> PeriodoResponse:
        periodo = self._get_periodo_record(session=session, periodo_id=periodo_id)
        return self._build_periodo_response(periodo)

    def get_active_periodo(self, *, session: Session) -> PeriodoResponse:
        periodo = self._get_active_periodo_record(session=session)
        return self._build_periodo_response(periodo)

    def get_cronograma(
        self,
        *,
        session: Session,
        current_user: UserRecord,
        orientando_id: str | None = None,
    ) -> CronogramaPeriodoResponse:
        periodo = self._get_active_periodo_record(session=session)

        if current_user.perfil == Perfil.ALUNO:
            return self._build_student_cronograma(
                session=session,
                periodo=periodo,
                current_user=current_user,
            )

        if current_user.perfil == Perfil.ORIENTADOR:
            return self._build_advisor_cronograma(
                session=session,
                periodo=periodo,
                current_user=current_user,
                orientando_id=orientando_id,
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=CRONOGRAMA_FORBIDDEN_DETAIL,
        )

    def update_periodo(
        self,
        *,
        session: Session,
        periodo_id: str,
        payload: UpdatePeriodoRequest,
        current_user: UserRecord,
    ) -> PeriodoResponse:
        periodo = self._get_periodo_record(session=session, periodo_id=periodo_id)
        if periodo.ativo is not True:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=INACTIVE_PERIOD_EDIT_DETAIL,
            )

        merged_payload = self._build_merged_payload(periodo=periodo, payload=payload)

        self._ensure_no_date_overlap(
            session=session,
            data_inicio=merged_payload.data_inicio,
            data_fim=merged_payload.data_fim,
            exclude_periodo_id=periodo.id,
        )
        if merged_payload.ativo:
            self._ensure_single_active_period(session=session, exclude_periodo_id=periodo.id)

        periodo.nome = merged_payload.nome
        periodo.data_inicio = merged_payload.data_inicio
        periodo.data_fim = merged_payload.data_fim
        periodo.ativo = merged_payload.ativo

        if payload.prazos is not None:
            periodo.prazos.clear()
            periodo.prazos.extend(self._build_prazos(merged_payload.prazos))

            AuditService().log_event(
                session=session,
                user_id=current_user.id,
                action="UPDATE_PRAZOS",
                entity="PERIODO",
                data={
                    "periodo_id": periodo.id,
                    "prazos": [
                        {
                            "nome_etapa": prazo.nome_etapa,
                            "data_limite": str(prazo.data_limite),
                            "tipo_tcc": prazo.tipo_tcc.value,
                        }
                        for prazo in periodo.prazos
                    ],
                },
            )

        self._persist_periodo(
            session=session,
            periodo=periodo,
            active_requested=merged_payload.ativo,
            data_inicio=merged_payload.data_inicio,
            data_fim=merged_payload.data_fim,
        )
        return self.get_periodo_by_id(session=session, periodo_id=periodo.id)

    def _get_periodo_record(self, *, session: Session, periodo_id: str) -> PeriodoLetivoRecord:
        periodo = session.scalar(
            select(PeriodoLetivoRecord)
            .options(selectinload(PeriodoLetivoRecord.prazos))
            .where(PeriodoLetivoRecord.id == periodo_id)
        )
        if periodo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=PERIODO_NOT_FOUND_DETAIL,
            )
        return periodo

    def _get_active_periodo_record(self, *, session: Session) -> PeriodoLetivoRecord:
        periodo = session.scalar(
            select(PeriodoLetivoRecord)
            .options(selectinload(PeriodoLetivoRecord.prazos))
            .where(PeriodoLetivoRecord.ativo.is_(True))
            .order_by(PeriodoLetivoRecord.data_inicio.desc())
        )
        if periodo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NO_ACTIVE_PERIODO_FOUND_DETAIL,
            )
        return periodo

    def _ensure_single_active_period(
        self,
        *,
        session: Session,
        exclude_periodo_id: str | None = None,
    ) -> None:
        query = select(PeriodoLetivoRecord).where(PeriodoLetivoRecord.ativo.is_(True))
        if exclude_periodo_id is not None:
            query = query.where(PeriodoLetivoRecord.id != exclude_periodo_id)

        existing_periodo = session.scalar(query)
        if existing_periodo is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ACTIVE_PERIOD_CONFLICT_DETAIL,
            )

    def _ensure_no_date_overlap(
        self,
        *,
        session: Session,
        data_inicio,
        data_fim,
        exclude_periodo_id: str | None = None,
    ) -> None:
        query = select(PeriodoLetivoRecord).where(
            PeriodoLetivoRecord.data_inicio <= data_fim,
            PeriodoLetivoRecord.data_fim >= data_inicio,
        )
        if exclude_periodo_id is not None:
            query = query.where(PeriodoLetivoRecord.id != exclude_periodo_id)

        overlapping_periodo = session.scalar(query)
        if overlapping_periodo is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=OVERLAPPING_PERIOD_CONFLICT_DETAIL,
            )

    def _persist_periodo(
        self,
        *,
        session: Session,
        periodo: PeriodoLetivoRecord,
        active_requested: bool,
        data_inicio,
        data_fim,
    ) -> None:
        session.add(periodo)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            if active_requested:
                self._ensure_single_active_period(session=session, exclude_periodo_id=periodo.id)
            self._ensure_no_date_overlap(
                session=session,
                data_inicio=data_inicio,
                data_fim=data_fim,
                exclude_periodo_id=periodo.id,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=PERIODO_SAVE_CONFLICT_DETAIL,
            ) from exc

    def _build_prazos(self, prazos: list[PrazoPayload]) -> list[PrazoEtapaRecord]:
        return [
            PrazoEtapaRecord(
                id=str(uuid4()),
                nome_etapa=prazo.nome_etapa,
                data_limite=prazo.data_limite,
                tipo_tcc=prazo.tipo_tcc,
            )
            for prazo in prazos
        ]

    def _build_merged_payload(
        self,
        *,
        periodo: PeriodoLetivoRecord,
        payload: UpdatePeriodoRequest,
    ) -> PeriodoWriteRequest:
        try:
            return PeriodoWriteRequest(
                nome=payload.nome if payload.nome is not None else periodo.nome,
                data_inicio=payload.data_inicio if payload.data_inicio is not None else periodo.data_inicio,
                data_fim=payload.data_fim if payload.data_fim is not None else periodo.data_fim,
                ativo=payload.ativo if payload.ativo is not None else periodo.ativo,
                prazos=payload.prazos if payload.prazos is not None else self._serialize_existing_prazos(periodo.prazos),
            )
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors()[0]["msg"],
            ) from exc

    def _serialize_existing_prazos(self, prazos: list[PrazoEtapaRecord]) -> list[PrazoPayload]:
        return [
            PrazoPayload(
                nome_etapa=prazo.nome_etapa,
                data_limite=prazo.data_limite,
                tipo_tcc=prazo.tipo_tcc,
            )
            for prazo in prazos
        ]

    def _build_periodo_response(self, periodo: PeriodoLetivoRecord) -> PeriodoResponse:
        ordered_prazos = self._order_prazos(periodo.prazos)
        return PeriodoResponse(
            id=periodo.id,
            nome=periodo.nome,
            data_inicio=periodo.data_inicio,
            data_fim=periodo.data_fim,
            ativo=periodo.ativo,
            prazos=[PrazoResponse.model_validate(prazo) for prazo in ordered_prazos],
        )

    def _build_student_cronograma(
        self,
        *,
        session: Session,
        periodo: PeriodoLetivoRecord,
        current_user: UserRecord,
    ) -> CronogramaPeriodoResponse:
        tcc = session.scalar(
            select(TCCRecord).where(
                TCCRecord.aluno_id == current_user.id,
                TCCRecord.periodo_id == periodo.id,
            )
        )
        tipo_tcc = tcc.tipo_tcc if tcc is not None else None
        prazos = self._filter_prazos_for_tipo(periodo.prazos, tipo_tcc=tipo_tcc)

        return CronogramaPeriodoResponse(
            periodo=self._build_periodo_summary(periodo),
            perfil=current_user.perfil,
            aluno=CronogramaAlunoResponse(
                aluno_id=current_user.id,
                titulo_tcc=tcc.titulo if tcc is not None else None,
                tipo_tcc=tipo_tcc,
                status_tcc=tcc.status if tcc is not None else None,
                prazo_excedido=tcc.prazo_excedido if tcc is not None else False,
                alerta_prazo=self._build_prazo_excedido_alert(tcc),
                prazos=[self._build_cronograma_prazo_response(prazo) for prazo in prazos],
            ),
        )

    def _build_advisor_cronograma(
        self,
        *,
        session: Session,
        periodo: PeriodoLetivoRecord,
        current_user: UserRecord,
        orientando_id: str | None,
    ) -> CronogramaPeriodoResponse:
        query = (
            select(TCCRecord, UserRecord)
            .join(UserRecord, UserRecord.id == TCCRecord.aluno_id)
            .where(
                TCCRecord.periodo_id == periodo.id,
                TCCRecord.status.in_(
                    [
                        StatusTCC.AGUARDANDO_ACEITE,
                        StatusTCC.EM_ANDAMENTO,
                        StatusTCC.APROVADO,
                    ]
                ),
                or_(
                    TCCRecord.orientador_id == current_user.id,
                    TCCRecord.coorientador_id == current_user.id,
                ),
            )
            .order_by(UserRecord.nome_completo.asc(), TCCRecord.criado_em.asc())
        )
        if orientando_id is not None:
            query = query.where(TCCRecord.aluno_id == orientando_id)

        rows = session.execute(query).all()
        if orientando_id is not None and not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ORIENTANDO_NOT_FOUND_DETAIL,
            )

        orientandos = []
        for tcc, aluno in rows:
            papel_orientacao = "ORIENTADOR" if tcc.orientador_id == current_user.id else "COORIENTADOR"
            prazos = self._filter_prazos_for_tipo(periodo.prazos, tipo_tcc=tcc.tipo_tcc)
            orientandos.append(
                CronogramaOrientandoResponse(
                    aluno_id=aluno.id,
                    aluno_nome=aluno.nome_completo,
                    matricula=aluno.matricula,
                    titulo_tcc=tcc.titulo,
                    tipo_tcc=tcc.tipo_tcc,
                    status_tcc=tcc.status,
                    prazo_excedido=tcc.prazo_excedido,
                    alerta_prazo=self._build_prazo_excedido_alert(tcc),
                    papel_orientacao=papel_orientacao,
                    prazos=[self._build_cronograma_prazo_response(prazo) for prazo in prazos],
                )
            )

        return CronogramaPeriodoResponse(
            periodo=self._build_periodo_summary(periodo),
            perfil=current_user.perfil,
            orientandos=orientandos,
            filtro_orientando_id=orientando_id,
        )

    def _build_periodo_summary(self, periodo: PeriodoLetivoRecord) -> PeriodoResumoResponse:
        return PeriodoResumoResponse(
            id=periodo.id,
            nome=periodo.nome,
            data_inicio=periodo.data_inicio,
            data_fim=periodo.data_fim,
            ativo=periodo.ativo,
        )

    def _build_cronograma_prazo_response(self, prazo: PrazoEtapaRecord) -> CronogramaPrazoResponse:
        dias_restantes = (prazo.data_limite - date.today()).days
        status_label, cor = self._status_info(dias_restantes)
        return CronogramaPrazoResponse(
            id=prazo.id,
            nome_etapa=prazo.nome_etapa,
            data_limite=prazo.data_limite,
            tipo_tcc=prazo.tipo_tcc,
            dias_restantes=dias_restantes,
            status=status_label,
            cor=cor,
            mensagem=self._formatar_mensagem(dias_restantes),
            atrasado=dias_restantes < 0,
        )

    def _filter_prazos_for_tipo(
        self,
        prazos: list[PrazoEtapaRecord],
        *,
        tipo_tcc: TipoTCC | None,
    ) -> list[PrazoEtapaRecord]:
        return [
            prazo
            for prazo in self._order_prazos(prazos)
            if prazo.tipo_tcc == TipoTCC.TODOS or (tipo_tcc is not None and prazo.tipo_tcc == tipo_tcc)
        ]

    def _build_prazo_excedido_alert(self, tcc: TCCRecord | None) -> str | None:
        if tcc is None or tcc.prazo_excedido is not True:
            return None
        return "Envio do TCC registrado fora do prazo configurado para tema/orientador."

    def _order_prazos(self, prazos: list[PrazoEtapaRecord]) -> list[PrazoEtapaRecord]:
        return sorted(
            prazos,
            key=lambda prazo: (prazo.data_limite, prazo.nome_etapa.casefold(), prazo.id),
        )

    def _status_info(self, dias_restantes: int) -> tuple[str, str]:
        if dias_restantes > 7:
            return "A_VENCER", "verde"
        if 1 <= dias_restantes <= 7:
            return "PROXIMO", "amarelo"
        if dias_restantes == 0:
            return "HOJE", "laranja"
        return "VENCIDO", "vermelho"

    def _formatar_mensagem(self, dias_restantes: int) -> str:
        if dias_restantes > 0:
            return f"Faltam {dias_restantes} dias"
        if dias_restantes == 0:
            return "Vence hoje"
        return f"Vencido ha {abs(dias_restantes)} dias"


async def get_periodo_service() -> PeriodoService:
    return PeriodoService()
