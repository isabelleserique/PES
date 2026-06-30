from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_authenticated_user, require_perfis
from backend.app.db.models import UserRecord
from backend.app.db.session import get_db_session
from backend.app.models.user import Perfil
from backend.app.schemas.banca import BancaRequest, BancaResponse
from backend.app.services.audit_service import AuditService, get_audit_service
from backend.app.services.banca_service import BancaService, get_banca_service
from backend.app.services.email_service import EmailService, get_email_service

router = APIRouter(prefix="/defesas", tags=["defesas"])


@router.post(
    "/banca",
    status_code=status.HTTP_200_OK,
)
async def registrar_banca(
    payload: BancaRequest,
    session: Session = Depends(get_db_session),
    banca_service: BancaService = Depends(get_banca_service),
    email_service: EmailService = Depends(get_email_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_orientador: UserRecord = Depends(require_perfis(Perfil.ORIENTADOR)),
) -> BancaResponse:
    return banca_service.registrar_banca(
        session=session,
        current_user=current_orientador,
        payload=payload,
        email_service=email_service,
        audit_service=audit_service,
    )


@router.get(
    "/banca",
    status_code=status.HTTP_200_OK,
)
async def buscar_banca(
    aluno_id: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
    banca_service: BancaService = Depends(get_banca_service),
    current_user: UserRecord = Depends(get_current_authenticated_user),
) -> BancaResponse | None:
    return banca_service.get_banca(
        session=session,
        current_user=current_user,
        aluno_id=aluno_id,
    )
