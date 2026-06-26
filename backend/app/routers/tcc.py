from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.models import UserRecord
from backend.app.db.session import get_db_session
from backend.app.models.user import Perfil
from backend.app.schemas.tcc import (
    OrientadorDisponivelResponse,
    OrientationDecisionRequest,
    OrientationDecisionResponse,
    OrientationRequestResponse,
    TCCResponse,
    TCCWriteRequest,
)
from backend.app.services.audit_service import AuditService, get_audit_service
from backend.app.services.email_service import EmailService, get_email_service
from backend.app.services.tcc_service import TCCService, get_tcc_service
from backend.app.schemas.tcc import BancaRequest, BancaResponse
from backend.app.api.deps import (
    require_perfis,
    get_current_authenticated_user,
)


router = APIRouter(prefix="/tcc", tags=["tcc"])


@router.get(
    "/orientadores",
    status_code=status.HTTP_200_OK,
)
async def list_active_orientadores(
    session: Session = Depends(get_db_session),
    tcc_service: TCCService = Depends(get_tcc_service),
    current_aluno: UserRecord = Depends(require_perfis(Perfil.ALUNO)),
) -> list[OrientadorDisponivelResponse]:
    _ = current_aluno
    return tcc_service.list_available_advisors(session=session)


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
)
async def get_my_tcc(
    session: Session = Depends(get_db_session),
    tcc_service: TCCService = Depends(get_tcc_service),
    current_aluno: UserRecord = Depends(require_perfis(Perfil.ALUNO)),
) -> TCCResponse:
    return tcc_service.get_my_tcc(session=session, current_user=current_aluno)


@router.post(
    "/me",
    status_code=status.HTTP_201_CREATED,
)
async def create_my_tcc(
    payload: TCCWriteRequest,
    session: Session = Depends(get_db_session),
    tcc_service: TCCService = Depends(get_tcc_service),
    email_service: EmailService = Depends(get_email_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_aluno: UserRecord = Depends(require_perfis(Perfil.ALUNO)),
) -> TCCResponse:
    return tcc_service.create_tcc(
        session=session,
        payload=payload,
        current_user=current_aluno,
        email_service=email_service,
        audit_service=audit_service,
    )


@router.patch(
    "/me",
    status_code=status.HTTP_200_OK,
)
async def update_my_tcc(
    payload: TCCWriteRequest,
    session: Session = Depends(get_db_session),
    tcc_service: TCCService = Depends(get_tcc_service),
    email_service: EmailService = Depends(get_email_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_aluno: UserRecord = Depends(require_perfis(Perfil.ALUNO)),
) -> TCCResponse:
    return tcc_service.update_my_tcc(
        session=session,
        payload=payload,
        current_user=current_aluno,
        email_service=email_service,
        audit_service=audit_service,
    )


@router.get(
    "/orientacoes/pendentes",
    status_code=status.HTTP_200_OK,
)
async def list_pending_orientation_requests(
    session: Session = Depends(get_db_session),
    tcc_service: TCCService = Depends(get_tcc_service),
    current_orientador: UserRecord = Depends(require_perfis(Perfil.ORIENTADOR)),
) -> list[OrientationRequestResponse]:
    return tcc_service.list_pending_orientation_requests(
        session=session,
        current_user=current_orientador,
    )


@router.patch(
    "/orientacoes/{tcc_id}/decisao",
    status_code=status.HTTP_200_OK,
)
async def decide_orientation_request(
    tcc_id: str,
    payload: OrientationDecisionRequest,
    session: Session = Depends(get_db_session),
    tcc_service: TCCService = Depends(get_tcc_service),
    email_service: EmailService = Depends(get_email_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_orientador: UserRecord = Depends(require_perfis(Perfil.ORIENTADOR)),
) -> OrientationDecisionResponse:
    return tcc_service.decide_orientation_request(
        session=session,
        tcc_id=tcc_id,
        payload=payload,
        current_user=current_orientador,
        email_service=email_service,
        audit_service=audit_service,
    )

@router.post(
    "/{tcc_id}/banca",
    status_code=200,
)
async def register_banca(
    tcc_id: str,
    payload: BancaRequest,
    session: Session = Depends(get_db_session),
    tcc_service: TCCService = Depends(get_tcc_service),
    current_orientador: UserRecord = Depends(require_perfis(Perfil.ORIENTADOR)),
) -> BancaResponse:
    return tcc_service.register_banca(
        session=session,
        tcc_id=tcc_id,
        payload=payload,
        current_user=current_orientador,
    )


@router.get(
    "/{tcc_id}/banca",
    status_code=200,
)
async def get_banca(
    tcc_id: str,
    session: Session = Depends(get_db_session),
    tcc_service: TCCService = Depends(get_tcc_service),
    current_user: UserRecord = Depends(get_current_authenticated_user),
) -> BancaResponse:
    return tcc_service.get_banca(
        session=session,
        tcc_id=tcc_id,
        current_user=current_user,
    )
