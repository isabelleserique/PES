from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db_session, get_current_authenticated_user
from backend.app.services.tcc_service import TCCService
from backend.app.services.email_service import get_email_service, EmailService
from backend.app.services.audit_service import get_audit_service, AuditService
from backend.app.schemas.tcc import TCCCreateRequest

router = APIRouter(prefix="/tcc", tags=["TCC"])


@router.post("/")
def create_tcc(
    payload: TCCCreateRequest,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_authenticated_user),
    email_service: EmailService = Depends(get_email_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    service = TCCService()
    return service.create_tcc(
        session=session,
        payload=payload,
        current_user=current_user,
        email_service=email_service,
        audit_service=audit_service,
    )

@router.put("/{tcc_id}")
def update_tcc(
    tcc_id: str,
    payload: TCCCreateRequest,
    session: Session = Depends(get_db_session),
    current_user=Depends(get_current_authenticated_user),
    audit_service: AuditService = Depends(get_audit_service),
):
    service = TCCService()
    return service.update_tcc(
        tcc_id=tcc_id,
        payload=payload,
        session=session,
        current_user=current_user,
        audit_service=audit_service,
    )