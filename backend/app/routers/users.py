from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db_session
from backend.app.schemas.user import CoordenadorCreateRequest, UserCreatedResponse
from backend.app.services.audit_service import AuditService, get_audit_service
from backend.app.services.email_service import EmailService, get_email_service
from backend.app.services.user_service import UserService, get_user_service

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


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
