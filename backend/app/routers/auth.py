from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db_session
from backend.app.schemas.auth import LoginRequest, PasswordResetConfirmRequest, PasswordResetRequest
from backend.app.services.audit_service import AuditService, get_audit_service
from backend.app.services.auth_service import AuthService, get_auth_service
from backend.app.services.email_service import EmailService, get_email_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
)
async def login(
    payload: LoginRequest,
    session: Session = Depends(get_db_session),
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> dict:
    response = auth_service.login(
        session=session,
        payload=payload,
        audit_service=audit_service,
    )
    return response.model_dump()


@router.post(
    "/esqueceu-senha",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@router.post(
    "/solicitar-reset",
    status_code=status.HTTP_200_OK,
)
async def request_password_reset(
    payload: PasswordResetRequest,
    session: Session = Depends(get_db_session),
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service),
) -> dict[str, str]:
    response = auth_service.request_password_reset(
        session=session,
        payload=payload,
        email_service=email_service,
    )
    return response.model_dump()


@router.post(
    "/redefinir-senha",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@router.post(
    "/confirmar-reset",
    status_code=status.HTTP_200_OK,
)
async def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    session: Session = Depends(get_db_session),
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> dict[str, str]:
    response = auth_service.confirm_password_reset(
        session=session,
        payload=payload,
        audit_service=audit_service,
    )
    return response.model_dump()
