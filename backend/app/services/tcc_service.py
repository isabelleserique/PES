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
from backend.app.schemas.tcc import (
    OrientadorDisponivelResponse,
    OrientationDecisionRequest,
    OrientationDecisionResponse,
    OrientationRequestResponse,
    TCCResponse,
    TCCWriteRequest,
)
from backend.app.services.audit_service import AuditService
from backend.app.services.email_service import EmailService

NO_ACTIVE_PERIODO_FOUND_DETAIL = "Nenhum periodo letivo ativo encontrado."
TCC_ALREADY_EXISTS_DETAIL = "Aluno ja informou um TCC neste periodo. Use a edicao para atualizar os dados."
TCC_NOT_FOUND_DETAIL = "Nenhum TCC informado para o periodo letivo ativo."
TCC_NOT_FOUND_FOR_ORIENTADOR_DETAIL = "Solicitacao de orientacao nao encontrada."
INVALID_ORIENTADOR_DETAIL = "Orientador informado nao foi encontrado ou nao esta ativo."
INVALID_COORIENTADOR_DETAIL = "Coorientador informado nao foi encontrado ou nao esta ativo."
ORIENTATION_REQUEST_NOT_PENDING_DETAIL = "Solicitacao de orientacao nao esta pendente."
SUBMISSION_DEADLINE_NAMES = {
    "definicao de tema/orientador",
    "definicao de tema e orientador",
    "indicacao de tema/orientador",
    "indicacao de tema e orientador",
    "indicar tema e orientador",
}
ORIENTATION_DECISION_DEADLINE_NAMES = {
    "aceite do orientador",
    "aceite de orientador",
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

    def list_pending_orientation_requests(
        self,
        *,
        session: Session,
        current_user: UserRecord,
    ) -> list[OrientationRequestResponse]:
        periodo = self._get_active_periodo_record(session=session)
        rows = session.execute(
            select(TCCRecord, UserRecord)
            .join(UserRecord, UserRecord.id == TCCRecord.aluno_id)
            .where(
                TCCRecord.periodo_id == periodo.id,
                TCCRecord.orientador_id == current_user.id,
                TCCRecord.status == StatusTCC.AGUARDANDO_ACEITE,
            )
            .order_by(TCCRecord.criado_em.asc(), UserRecord.nome_completo.asc())
        ).all()

        return [
            self._build_orientation_request_response(
                tcc=tcc,
                aluno=aluno,
                periodo=periodo,
            )
            for tcc, aluno in rows
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

    def decide_orientation_request(
        self,
        *,
        session: Session,
        tcc_id: str,
        payload: OrientationDecisionRequest,
        current_user: UserRecord,
        email_service: EmailService,
        audit_service: AuditService,
    ) -> OrientationDecisionResponse:
        tcc = session.scalar(
            select(TCCRecord).where(
                TCCRecord.id == tcc_id,
                TCCRecord.orientador_id == current_user.id,
            )
        )
        if tcc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=TCC_NOT_FOUND_FOR_ORIENTADOR_DETAIL,
            )
        if tcc.status != StatusTCC.AGUARDANDO_ACEITE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ORIENTATION_REQUEST_NOT_PENDING_DETAIL,
            )

        periodo = self._get_active_periodo_record(session=session)
        if tcc.periodo_id != periodo.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ORIENTATION_REQUEST_NOT_PENDING_DETAIL,
            )

        aluno = session.scalar(select(UserRecord).where(UserRecord.id == tcc.aluno_id))
        if aluno is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aluno relacionado ao TCC nao foi encontrado.",
            )

        previous_snapshot = self._serialize_tcc_snapshot(
            tcc=tcc,
            periodo=periodo,
            orientador=current_user,
            coorientador=self._get_professor_by_id(session=session, user_id=tcc.coorientador_id),
        )
        acao_fora_do_prazo, alerta_acao_prazo, _ = self._build_orientation_deadline_info(
            periodo=periodo,
            tipo_tcc=tcc.tipo_tcc,
        )

        if payload.acao == "ACEITAR":
            tcc.status = StatusTCC.EM_ANDAMENTO
            log_action = AcaoEdicaoTCC.ACEITE_ORIENTACAO
            accepted = True
        else:
            tcc.status = StatusTCC.SEM_ORIENTADOR
            log_action = AcaoEdicaoTCC.RECUSA_ORIENTACAO
            accepted = False

        tcc.observacao_orientador = payload.observacao

        session.add(
            self._build_edit_log(
                tcc=tcc,
                actor_user_id=current_user.id,
                action=log_action,
                previous_snapshot=previous_snapshot,
                periodo=periodo,
                orientador=current_user,
                coorientador=self._get_professor_by_id(session=session, user_id=tcc.coorientador_id),
                observacao=payload.observacao,
            )
        )
        session.commit()
        session.refresh(tcc)

        email_service.send_orientation_decision_notification(
            to_email=aluno.email,
            aluno_nome=aluno.nome_completo,
            titulo=tcc.titulo,
            orientador_nome=current_user.nome_completo,
            accepted=accepted,
            observacao=payload.observacao,
            outside_deadline=acao_fora_do_prazo,
        )
        audit_service.log_orientation_decision(
            actor_user_id=current_user.id,
            aluno_id=aluno.id,
            tcc_id=tcc.id,
            decision=payload.acao,
            resulting_status=tcc.status.value,
            outside_deadline=acao_fora_do_prazo,
        )
        return OrientationDecisionResponse(
            tcc_id=tcc.id,
            aluno_id=aluno.id,
            aluno_nome=aluno.nome_completo,
            status=tcc.status,
            observacao_orientador=tcc.observacao_orientador,
            acao_fora_do_prazo=acao_fora_do_prazo,
            alerta_acao_prazo=alerta_acao_prazo,
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
        tcc.observacao_orientador = None

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
        return self._find_deadline(
            periodo=periodo,
            tipo_tcc=tipo_tcc,
            accepted_names=SUBMISSION_DEADLINE_NAMES,
        )

    def _find_orientation_deadline(
        self,
        *,
        periodo: PeriodoLetivoRecord,
        tipo_tcc: TipoTCC,
    ) -> PrazoEtapaRecord | None:
        return self._find_deadline(
            periodo=periodo,
            tipo_tcc=tipo_tcc,
            accepted_names=ORIENTATION_DECISION_DEADLINE_NAMES,
        )

    def _find_deadline(
        self,
        *,
        periodo: PeriodoLetivoRecord,
        tipo_tcc: TipoTCC,
        accepted_names: set[str],
    ) -> PrazoEtapaRecord | None:
        matching_prazos = [
            prazo
            for prazo in periodo.prazos
            if prazo.tipo_tcc in {TipoTCC.TODOS, tipo_tcc}
            and prazo.nome_etapa.strip().casefold() in accepted_names
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
        observacao: str | None = None,
    ) -> TCCEditLogRecord:
        return TCCEditLogRecord(
            id=str(uuid4()),
            tcc=tcc,
            actor_user_id=actor_user_id,
            acao=action,
            observacao=observacao,
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
            "observacao_orientador": tcc.observacao_orientador,
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
            observacao_orientador=tcc.observacao_orientador,
            criado_em=tcc.criado_em,
            atualizado_em=tcc.atualizado_em,
        )

    def _build_orientation_request_response(
        self,
        *,
        tcc: TCCRecord,
        aluno: UserRecord,
        periodo: PeriodoLetivoRecord,
    ) -> OrientationRequestResponse:
        acao_fora_do_prazo, alerta_acao_prazo, prazo_aceite = self._build_orientation_deadline_info(
            periodo=periodo,
            tipo_tcc=tcc.tipo_tcc,
        )
        alerta_submissao = None
        if tcc.prazo_excedido:
            alerta_submissao = "Solicitacao enviada pelo aluno fora do prazo configurado."

        return OrientationRequestResponse(
            tcc_id=tcc.id,
            aluno_id=aluno.id,
            aluno_nome=aluno.nome_completo,
            aluno_email=aluno.email,
            matricula=aluno.matricula,
            titulo=tcc.titulo,
            tipo_tcc=tcc.tipo_tcc,
            status=tcc.status,
            prazo_excedido=tcc.prazo_excedido,
            alerta_submissao_prazo=alerta_submissao,
            prazo_aceite=prazo_aceite,
            acao_fora_do_prazo=acao_fora_do_prazo,
            alerta_acao_prazo=alerta_acao_prazo,
            criado_em=tcc.criado_em,
        )

    def _build_orientation_deadline_info(
        self,
        *,
        periodo: PeriodoLetivoRecord,
        tipo_tcc: TipoTCC,
    ) -> tuple[bool, str | None, date | None]:
        prazo = self._find_orientation_deadline(periodo=periodo, tipo_tcc=tipo_tcc)
        if prazo is None:
            return False, None, None

        days_late = (date.today() - prazo.data_limite).days
        if days_late > 0:
            return True, f"Aceite registrado fora do prazo ha {days_late} dia(s).", prazo.data_limite
        if days_late == 0:
            return False, "Prazo final de aceite: hoje.", prazo.data_limite
        return False, f"Prazo de aceite ate {prazo.data_limite.isoformat()}.", prazo.data_limite


async def get_tcc_service() -> TCCService:
    return TCCService()
