import logging
from datetime import UTC, datetime

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

async def get_audit_service() -> AuditService:
    return AuditService()
