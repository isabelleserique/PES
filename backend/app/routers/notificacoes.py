from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_active_coordenador, get_current_authenticated_user
from backend.app.db.models import UserRecord
from backend.app.db.session import get_db_session
from backend.app.schemas.notificacao import NotificacaoPrazoResultado
from backend.app.schemas.preferencias import PreferenciasNotificacao
from backend.app.services.email_service import EmailService, get_email_service
from backend.app.services.notificacao_service import NotificacaoPrazoService, get_notificacao_prazo_service

router = APIRouter(prefix="/notificacoes", tags=["notificacoes"])


@router.get(
    "/preferencias",
    status_code=status.HTTP_200_OK,
)
async def get_preferencias_notificacao(
    current_user: UserRecord = Depends(get_current_authenticated_user),
) -> PreferenciasNotificacao:
    return PreferenciasNotificacao(
        email_prazos_orientandos=current_user.email_prazos_orientandos,
        antecedencia_dias=current_user.notificacao_antecedencia_dias,
        email_notas_parciais=current_user.email_notas_parciais,
        email_notas_finais=current_user.email_notas_finais,
    )


@router.put(
    "/preferencias",
    status_code=status.HTTP_200_OK,
)
async def salvar_preferencias_notificacao(
    payload: PreferenciasNotificacao,
    session: Session = Depends(get_db_session),
    current_user: UserRecord = Depends(get_current_authenticated_user),
) -> PreferenciasNotificacao:
    current_user.email_prazos_orientandos = payload.email_prazos_orientandos
    current_user.notificacao_antecedencia_dias = payload.antecedencia_dias
    current_user.email_notas_parciais = payload.email_notas_parciais
    current_user.email_notas_finais = payload.email_notas_finais
    session.commit()
    session.refresh(current_user)
    return PreferenciasNotificacao(
        email_prazos_orientandos=current_user.email_prazos_orientandos,
        antecedencia_dias=current_user.notificacao_antecedencia_dias,
        email_notas_parciais=current_user.email_notas_parciais,
        email_notas_finais=current_user.email_notas_finais,
    )


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
