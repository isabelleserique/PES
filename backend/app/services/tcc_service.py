from __future__ import annotations

from datetime import date
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models import (
    PeriodoLetivoRecord,
    PrazoEtapaRecord,
    TCCEditLogRecord,
    TCCRecord,
    UserRecord,
)
from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import AcaoEdicaoTCC, StatusTCC
from backend.app.models.user import Perfil, StatusCadastro
from backend.app.schemas.tcc import OrientadorDisponivelResponse, TCCResponse, TCCWriteRequest
from backend.app.services.audit_service import AuditService
from backend.app.services.email_service import EmailService

NO_ACTIVE_PERIODO_FOUND_DETAIL = "Nenhum periodo letivo ativo encontrado."
TCC_ALREADY_EXISTS_DETAIL = "Aluno ja informou um TCC neste periodo. Use a edicao para atualizar os dados."
TCC_NOT_FOUND_DETAIL = "Nenhum TCC informado para o periodo letivo ativo."
INVALID_ORIENTADOR_DETAIL = "Orientador informado nao foi encontrado ou nao esta ativo."
INVALID_COORIENTADOR_DETAIL = "Coorientador informado nao foi encontrado ou nao esta ativo."
SUBMISSION_DEADLINE_NAMES = {
    "definicao de tema/orientador",
    "definicao de tema e orientador",
    "indicacao de tema/orientador",
    "indicacao de tema e orientador",
    "indicar tema e orientador",
}


class TCCService:
    def list_available_advisors(self, *, session: Session) -> list[OrientadorDisponivelResponse]:
        orientadores = session.scalars(
            select(UserRecord)
            .where(
                UserRecord.perfil == Perfil.ORIENTADOR,
                UserRecord.status == StatusCadastro.ATIVO,
                UserRecord.ativo.is_(True),
            )
            .order_by(UserRecord.nome_completo.asc())
        ).all()
        return [
            OrientadorDisponivelResponse(
                id=orientador.id,
                nome_completo=orientador.nome_completo,
                email=orientador.email,
            )
            for orientador in orientadores
        ]

    def get_my_tcc(
        self,
        *,
        session: Session,
        current_user: UserRecord,
    ) -> TCCResponse:
        periodo = self._get_active_periodo_record(session=session)
        tcc = self._get_tcc_record_for_student(
            session=session,
            aluno_id=current_user.id,
            periodo_id=periodo.id,
        )
        if tcc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=TCC_NOT_FOUND_DETAIL,
            )

        orientador = self._get_professor_by_id(session=session, user_id=tcc.orientador_id)
        coorientador = self._get_professor_by_id(session=session, user_id=tcc.coorientador_id)
        return self._build_tcc_response(
            tcc=tcc,
            periodo=periodo,
            orientador=orientador,
            coorientador=coorientador,
        )

    def create_tcc(
        self,
        *,
        session: Session,
        payload: TCCWriteRequest,
        current_user: UserRecord,
        email_service: EmailService,
        audit_service: AuditService,
    ) -> TCCResponse:
        periodo = self._get_active_periodo_record(session=session)
        existing_tcc = self._get_tcc_record_for_student(
            session=session,
            aluno_id=current_user.id,
            periodo_id=periodo.id,
        )
        if existing_tcc is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=TCC_ALREADY_EXISTS_DETAIL,
            )

        orientador = self._get_active_professor(session=session, user_id=payload.orientador_id)
        coorientador = self._get_optional_active_professor(session=session, user_id=payload.coorientador_id)
        prazo_excedido = self._is_submission_late(periodo=periodo, tipo_tcc=payload.tipo_tcc)

        tcc = TCCRecord(
            id=str(uuid4()),
            titulo=payload.titulo,
            tipo_tcc=payload.tipo_tcc,
            aluno_id=current_user.id,
            orientador_id=orientador.id,
            coorientador_id=coorientador.id if coorientador is not None else None,
            periodo_id=periodo.id,
            status=StatusTCC.AGUARDANDO_ACEITE,
            prazo_excedido=prazo_excedido,
        )
        session.add(tcc)
        session.add(
            self._build_edit_log(
                tcc=tcc,
                actor_user_id=current_user.id,
                action=AcaoEdicaoTCC.CRIACAO,
                previous_snapshot=None,
                periodo=periodo,
                orientador=orientador,
                coorientador=coorientador,
            )
        )
        session.commit()
        session.refresh(tcc)

        email_service.send_tcc_submission_notification(
            to_email=orientador.email,
            aluno_nome=current_user.nome_completo,
            titulo=tcc.titulo,
            tipo_tcc=tcc.tipo_tcc.value,
            periodo_nome=periodo.nome,
            prazo_excedido=tcc.prazo_excedido,
        )
        audit_service.log_tcc_submission(
            aluno_id=current_user.id,
            tcc_id=tcc.id,
            orientador_id=orientador.id,
            prazo_excedido=tcc.prazo_excedido,
        )
        return self._build_tcc_response(
            tcc=tcc,
            periodo=periodo,
            orientador=orientador,
            coorientador=coorientador,
        )

    def update_my_tcc(
        self,
        *,
        session: Session,
        payload: TCCWriteRequest,
        current_user: UserRecord,
        email_service: EmailService,
        audit_service: AuditService,
    ) -> TCCResponse:
        periodo = self._get_active_periodo_record(session=session)
        tcc = self._get_tcc_record_for_student(
            session=session,
            aluno_id=current_user.id,
            periodo_id=periodo.id,
        )
        if tcc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=TCC_NOT_FOUND_DETAIL,
            )

        previous_orientador = self._get_professor_by_id(session=session, user_id=tcc.orientador_id)
        previous_coorientador = self._get_professor_by_id(session=session, user_id=tcc.coorientador_id)
        previous_snapshot = self._serialize_tcc_snapshot(
            tcc=tcc,
            periodo=periodo,
            orientador=previous_orientador,
            coorientador=previous_coorientador,
        )

        orientador = self._get_active_professor(session=session, user_id=payload.orientador_id)
        coorientador = self._get_optional_active_professor(session=session, user_id=payload.coorientador_id)

        tcc.titulo = payload.titulo
        tcc.tipo_tcc = payload.tipo_tcc
        tcc.orientador_id = orientador.id
        tcc.coorientador_id = coorientador.id if coorientador is not None else None
        tcc.status = StatusTCC.AGUARDANDO_ACEITE
        tcc.prazo_excedido = self._is_submission_late(periodo=periodo, tipo_tcc=payload.tipo_tcc)

        session.add(
            self._build_edit_log(
                tcc=tcc,
                actor_user_id=current_user.id,
                action=AcaoEdicaoTCC.EDICAO,
                previous_snapshot=previous_snapshot,
                periodo=periodo,
                orientador=orientador,
                coorientador=coorientador,
            )
        )
        session.commit()
        session.refresh(tcc)

        email_service.send_tcc_submission_notification(
            to_email=orientador.email,
            aluno_nome=current_user.nome_completo,
            titulo=tcc.titulo,
            tipo_tcc=tcc.tipo_tcc.value,
            periodo_nome=periodo.nome,
            prazo_excedido=tcc.prazo_excedido,
        )
        audit_service.log_tcc_update(
            aluno_id=current_user.id,
            tcc_id=tcc.id,
            orientador_id=orientador.id,
            prazo_excedido=tcc.prazo_excedido,
        )
        return self._build_tcc_response(
            tcc=tcc,
            periodo=periodo,
            orientador=orientador,
            coorientador=coorientador,
        )

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

    def _get_tcc_record_for_student(
        self,
        *,
        session: Session,
        aluno_id: str,
        periodo_id: str,
    ) -> TCCRecord | None:
        return session.scalar(
            select(TCCRecord).where(
                TCCRecord.aluno_id == aluno_id,
                TCCRecord.periodo_id == periodo_id,
            )
        )

    def _get_active_professor(self, *, session: Session, user_id: str) -> UserRecord:
        professor = self._get_professor_by_id(session=session, user_id=user_id)
        if professor is None or professor.perfil != Perfil.ORIENTADOR:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=INVALID_ORIENTADOR_DETAIL,
            )
        if professor.status != StatusCadastro.ATIVO or professor.ativo is not True:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=INVALID_ORIENTADOR_DETAIL,
            )
        return professor

    def _get_optional_active_professor(
        self,
        *,
        session: Session,
        user_id: str | None,
    ) -> UserRecord | None:
        if user_id is None:
            return None

        professor = self._get_professor_by_id(session=session, user_id=user_id)
        if professor is None or professor.perfil != Perfil.ORIENTADOR:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=INVALID_COORIENTADOR_DETAIL,
            )
        if professor.status != StatusCadastro.ATIVO or professor.ativo is not True:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=INVALID_COORIENTADOR_DETAIL,
            )
        return professor

    def _get_professor_by_id(self, *, session: Session, user_id: str | None) -> UserRecord | None:
        if user_id is None:
            return None
        return session.scalar(select(UserRecord).where(UserRecord.id == user_id))

    def _is_submission_late(self, *, periodo: PeriodoLetivoRecord, tipo_tcc: TipoTCC) -> bool:
        prazo = self._find_submission_deadline(periodo=periodo, tipo_tcc=tipo_tcc)
        if prazo is None:
            return False
        return date.today() > prazo.data_limite

    def _find_submission_deadline(
        self,
        *,
        periodo: PeriodoLetivoRecord,
        tipo_tcc: TipoTCC,
    ) -> PrazoEtapaRecord | None:
        matching_prazos = [
            prazo
            for prazo in periodo.prazos
            if prazo.tipo_tcc in {TipoTCC.TODOS, tipo_tcc}
            and prazo.nome_etapa.strip().casefold() in SUBMISSION_DEADLINE_NAMES
        ]
        if not matching_prazos:
            return None
        return min(
            matching_prazos,
            key=lambda prazo: (prazo.data_limite, prazo.nome_etapa.casefold(), prazo.id),
        )

    def _build_edit_log(
        self,
        *,
        tcc: TCCRecord,
        actor_user_id: str,
        action: AcaoEdicaoTCC,
        previous_snapshot: dict | None,
        periodo: PeriodoLetivoRecord,
        orientador: UserRecord,
        coorientador: UserRecord | None,
    ) -> TCCEditLogRecord:
        return TCCEditLogRecord(
            id=str(uuid4()),
            tcc=tcc,
            actor_user_id=actor_user_id,
            acao=action,
            dados_anteriores=previous_snapshot,
            dados_novos=self._serialize_tcc_snapshot(
                tcc=tcc,
                periodo=periodo,
                orientador=orientador,
                coorientador=coorientador,
            ),
        )

    def _serialize_tcc_snapshot(
        self,
        *,
        tcc: TCCRecord,
        periodo: PeriodoLetivoRecord,
        orientador: UserRecord,
        coorientador: UserRecord | None,
    ) -> dict[str, str | bool | None]:
        return {
            "titulo": tcc.titulo,
            "tipo_tcc": tcc.tipo_tcc.value,
            "orientador_id": orientador.id,
            "orientador_nome": orientador.nome_completo,
            "coorientador_id": coorientador.id if coorientador is not None else None,
            "coorientador_nome": coorientador.nome_completo if coorientador is not None else None,
            "periodo_id": periodo.id,
            "periodo_nome": periodo.nome,
            "status": tcc.status.value,
            "prazo_excedido": tcc.prazo_excedido,
        }

    def _build_tcc_response(
        self,
        *,
        tcc: TCCRecord,
        periodo: PeriodoLetivoRecord,
        orientador: UserRecord,
        coorientador: UserRecord | None,
    ) -> TCCResponse:
        alerta = None
        if tcc.prazo_excedido:
            alerta = "Envio registrado fora do prazo configurado para tema/orientador."

        return TCCResponse(
            id=tcc.id,
            titulo=tcc.titulo,
            tipo_tcc=tcc.tipo_tcc,
            orientador_id=orientador.id,
            orientador_nome=orientador.nome_completo,
            coorientador_id=coorientador.id if coorientador is not None else None,
            coorientador_nome=coorientador.nome_completo if coorientador is not None else None,
            periodo_id=periodo.id,
            periodo_nome=periodo.nome,
            status=tcc.status,
            prazo_excedido=tcc.prazo_excedido,
            alerta_prazo=alerta,
            criado_em=tcc.criado_em,
            atualizado_em=tcc.atualizado_em,
        )


async def get_tcc_service() -> TCCService:
    return TCCService()
