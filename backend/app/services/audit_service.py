import logging
from datetime import UTC, datetime
from typing import Optional

from backend.app.models.user import Perfil, StatusCadastro

from sqlalchemy.orm import Session
from backend.app.db.models import AuditLogRecord
from uuid import uuid4

logger = logging.getLogger("backend.audit")


class AuditService:
    def log_user_registration(self, *, user_id: str, perfil: Perfil) -> None:
        timestamp = datetime.now(UTC).isoformat()
        logger.info(
            "AUDIT action=CADASTRO_USUARIO perfil=%s user_id=%s timestamp=%s",
            perfil.value,
            user_id,
            timestamp,
        )

    def log_registration_request(self, *, user_id: str, perfil: Perfil) -> None:
        timestamp = datetime.now(UTC).isoformat()
        logger.info(
            "AUDIT action=SOLICITACAO_CADASTRO perfil=%s status=%s user_id=%s timestamp=%s",
            perfil.value,
            StatusCadastro.PENDENTE.value,
            user_id,
            timestamp,
        )

    def log_registration_decision(
        self,
        *,
        session: Session,
        actor_user_id: str,
        target_user_id: str,
        decision: str,
        resulting_status: StatusCadastro,
    ) -> None:
        timestamp = datetime.now(UTC)
        log = AuditLogRecord(
            id=str(uuid4()),
            user_id=actor_user_id,
            acao="DECISAO_CADASTRO",
            entidade="USER",
            dados={
                "target_user_id": target_user_id,
                "decision": decision,
                "resulting_status": resulting_status.value,
            },
            ip=None,
        )

        session.add(log)
        session.commit()

        logger.info(
            "AUDIT_DB action=DECISAO_CADASTRO actor_user_id=%s target_user_id=%s status=%s timestamp=%s",
            actor_user_id,
            target_user_id,
            resulting_status.value,
            timestamp.isoformat(),
        )

    def log_login_failed(
        self,
        *,
        email: str,
        user_id: Optional[str] = None,
        attempt_count: Optional[int] = None,
        blocked_until: Optional[datetime] = None,
    ) -> None:
        timestamp = datetime.now(UTC).isoformat()
        logger.info(
            "AUDIT action=LOGIN_FAILED email=%s user_id=%s attempts=%s blocked_until=%s timestamp=%s",
            email,
            user_id,
            attempt_count,
            blocked_until.isoformat() if blocked_until else None,
            timestamp,
        )

    def log_login_success(self, *, user_id: str, perfil: Perfil) -> None:
        timestamp = datetime.now(UTC).isoformat()
        logger.info(
            "AUDIT action=LOGIN_SUCCESS user_id=%s perfil=%s timestamp=%s",
            user_id,
            perfil.value,
            timestamp,
        )

    def log_login_blocked(
        self,
        *,
        user_id: str,
        email: str,
        blocked_until: datetime,
    ) -> None:
        timestamp = datetime.now(UTC).isoformat()
        logger.info(
            "AUDIT action=LOGIN_BLOCKED user_id=%s email=%s blocked_until=%s timestamp=%s",
            user_id,
            email,
            blocked_until.isoformat(),
            timestamp,
        )

    def log_login_denied(self, *, user_id: str, email: str, reason: str) -> None:
        timestamp = datetime.now(UTC).isoformat()
        logger.info(
            "AUDIT action=LOGIN_DENIED user_id=%s email=%s reason=%s timestamp=%s",
            user_id,
            email,
            reason,
            timestamp,
        )

    def log_password_reset(self, *, user_id: str) -> None:
        timestamp = datetime.now(UTC).isoformat()
        logger.info(
            "AUDIT action=RESET_SENHA user_id=%s timestamp=%s",
            user_id,
            timestamp,
        )

    def log_tcc_submission(
        self,
        *,
        aluno_id: str,
        tcc_id: str,
        orientador_id: str,
        prazo_excedido: bool,
    ) -> None:
        timestamp = datetime.now(UTC).isoformat()
        logger.info(
            "AUDIT action=TCC_SUBMISSION aluno_id=%s tcc_id=%s orientador_id=%s prazo_excedido=%s timestamp=%s",
            aluno_id,
            tcc_id,
            orientador_id,
            prazo_excedido,
            timestamp,
        )

    def log_tcc_update(
        self,
        *,
        aluno_id: str,
        tcc_id: str,
        orientador_id: str,
        prazo_excedido: bool,
    ) -> None:
        timestamp = datetime.now(UTC).isoformat()
        logger.info(
            "AUDIT action=TCC_UPDATE aluno_id=%s tcc_id=%s orientador_id=%s prazo_excedido=%s timestamp=%s",
            aluno_id,
            tcc_id,
            orientador_id,
            prazo_excedido,
            timestamp,
        )

    def log_orientation_decision(
        self,
        *,
        actor_user_id: str,
        aluno_id: str,
        tcc_id: str,
        decision: str,
        resulting_status: str,
        outside_deadline: bool,
    ) -> None:
        timestamp = datetime.now(UTC).isoformat()
        logger.info(
            "AUDIT action=ORIENTATION_DECISION actor_user_id=%s aluno_id=%s tcc_id=%s decision=%s status=%s outside_deadline=%s timestamp=%s",
            actor_user_id,
            aluno_id,
            tcc_id,
            decision,
            resulting_status,
            outside_deadline,
            timestamp,
        )

    def log_event(
        self,
        *,
        session: Session,
        user_id: str | None,
        action: str,
        entity: str | None = None,
        data: dict | None = None,
        ip: str | None = None,
    ) -> None:
        log = AuditLogRecord(
            id=str(uuid4()),
            user_id=user_id,
            acao=action,
            entidade=entity,
            dados=data,
            ip=ip,
        )

        session.add(log)
        session.commit()

        logger.info(
            "AUDIT_DB action=%s user_id=%s entity=%s",
            action,
            user_id,
            entity,
        )

async def get_audit_service() -> AuditService:
    return AuditService()
