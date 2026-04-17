from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_active_coordenador, get_current_authenticated_user
from backend.app.db.models import UserRecord
from backend.app.db.session import get_db_session
from backend.app.schemas.user import (
    AuthenticatedUserProfileResponse,
    CadastroApprovalRequest,
    CoordenadorCreateRequest,
    PendingRegistrationResponse,
    SolicitarCadastroRequest,
)
from backend.app.services.audit_service import AuditService, get_audit_service
from backend.app.services.email_service import EmailService, get_email_service
from backend.app.services.user_service import UserService, get_user_service

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
)
async def get_authenticated_profile(
    user_service: UserService = Depends(get_user_service),
    current_user: UserRecord = Depends(get_current_authenticated_user),
) -> AuthenticatedUserProfileResponse:
    response = user_service.get_authenticated_profile(current_user=current_user)
    return response


@router.get(
    "/pendentes",
    status_code=status.HTTP_200_OK,
)
async def list_pending_registrations(
    session: Session = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
    current_coordenador: UserRecord = Depends(get_current_active_coordenador),
) -> list[PendingRegistrationResponse]:
    _ = current_coordenador
    response = user_service.list_pending_registrations(session=session)
    return response


@router.post(
    "/coordenador",
    status_code=status.HTTP_201_CREATED,
)
async def create_coordenador(
    payload: CoordenadorCreateRequest,
    session: Session = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
    email_service: EmailService = Depends(get_email_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> dict[str, str]:
    response = user_service.create_coordenador(
        session=session,
        payload=payload,
        email_service=email_service,
        audit_service=audit_service,
    )
    return response.model_dump()


@router.post(
    "/solicitar-cadastro",
    status_code=status.HTTP_201_CREATED,
)
async def request_registration(
    payload: SolicitarCadastroRequest,
    session: Session = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
    email_service: EmailService = Depends(get_email_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> dict[str, str]:
    response = user_service.request_registration(
        session=session,
        payload=payload,
        email_service=email_service,
        audit_service=audit_service,
    )
    return response.model_dump()


@router.patch(
    "/{user_id}/aprovar",
    status_code=status.HTTP_200_OK,
)
async def review_registration(
    user_id: str,
    payload: CadastroApprovalRequest,
    session: Session = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
    email_service: EmailService = Depends(get_email_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_coordenador: UserRecord = Depends(get_current_active_coordenador),
) -> dict[str, str]:
    response = user_service.review_registration(
        session=session,
        target_user_id=user_id,
        payload=payload,
        acted_by=current_coordenador,
        email_service=email_service,
        audit_service=audit_service,
    )
    return response.model_dump()
