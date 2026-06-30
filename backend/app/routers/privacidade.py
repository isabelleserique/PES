from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_authenticated_user
from backend.app.db.models import UserRecord
from backend.app.db.session import get_db_session
from backend.app.schemas.preferencias import ConsentimentoLgpd

router = APIRouter(prefix="/privacidade", tags=["privacidade"])


@router.get(
    "/consentimento",
    status_code=status.HTTP_200_OK,
)
async def get_consentimento_lgpd(
    current_user: UserRecord = Depends(get_current_authenticated_user),
) -> ConsentimentoLgpd:
    return ConsentimentoLgpd(
        publicar_portal_publico=current_user.publicar_tcc_portal_publico,
        compartilhar_terceiros=current_user.compartilhar_dados_terceiros,
        atualizado_em=current_user.privacidade_atualizado_em,
    )


@router.put(
    "/consentimento",
    status_code=status.HTTP_200_OK,
)
async def salvar_consentimento_lgpd(
    payload: ConsentimentoLgpd,
    session: Session = Depends(get_db_session),
    current_user: UserRecord = Depends(get_current_authenticated_user),
) -> ConsentimentoLgpd:
    current_user.publicar_tcc_portal_publico = payload.publicar_portal_publico
    current_user.compartilhar_dados_terceiros = payload.compartilhar_terceiros
    current_user.privacidade_atualizado_em = datetime.utcnow()
    session.commit()
    session.refresh(current_user)
    return ConsentimentoLgpd(
        publicar_portal_publico=current_user.publicar_tcc_portal_publico,
        compartilhar_terceiros=current_user.compartilhar_dados_terceiros,
        atualizado_em=current_user.privacidade_atualizado_em,
    )
