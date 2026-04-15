import logging
from datetime import UTC, datetime

from backend.app.models.user import Perfil

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

async def get_audit_service() -> AuditService:
    return AuditService()
