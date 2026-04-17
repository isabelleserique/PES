from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db_session
from backend.app.schemas.auth import LoginRequest
from backend.app.services.audit_service import AuditService, get_audit_service
from backend.app.services.auth_service import AuthService, get_auth_service

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
