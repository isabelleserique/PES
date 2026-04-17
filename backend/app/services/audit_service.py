import logging
from datetime import UTC, datetime
from typing import Optional

from backend.app.models.user import Perfil, StatusCadastro

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
        actor_user_id: str,
        target_user_id: str,
        decision: str,
        resulting_status: StatusCadastro,
    ) -> None:
        timestamp = datetime.now(UTC).isoformat()
        logger.info(
            "AUDIT action=DECISAO_CADASTRO decision=%s actor_user_id=%s target_user_id=%s status=%s timestamp=%s",
            decision,
            actor_user_id,
            target_user_id,
            resulting_status.value,
            timestamp,
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

async def get_audit_service() -> AuditService:
    return AuditService()
