from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_active_coordenador
from backend.app.db.models import UserRecord
from backend.app.db.session import get_db_session
from backend.app.schemas.notificacao import NotificacaoPrazoResultado
from backend.app.services.email_service import EmailService, get_email_service
from backend.app.services.notificacao_service import NotificacaoPrazoService, get_notificacao_prazo_service

router = APIRouter(prefix="/notificacoes", tags=["notificacoes"])


@router.post(
    "/prazos/processar",
    status_code=status.HTTP_200_OK,
)
async def processar_notificacoes_prazos(
    session: Session = Depends(get_db_session),
    notificacao_service: NotificacaoPrazoService = Depends(get_notificacao_prazo_service),
    email_service: EmailService = Depends(get_email_service),
    current_coordenador: UserRecord = Depends(get_current_active_coordenador),
) -> NotificacaoPrazoResultado:
    _ = current_coordenador
    return notificacao_service.processar_alertas_prazos(
        session=session,
        email_service=email_service,
    )
