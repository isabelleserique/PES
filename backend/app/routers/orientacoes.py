from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_perfis
from backend.app.db.models import UserRecord
from backend.app.db.session import get_db_session
from backend.app.models.user import Perfil
from backend.app.schemas.orientacao import SessaoOrientacaoPayload, SessaoOrientacaoResponse
from backend.app.services.audit_service import AuditService, get_audit_service
from backend.app.services.orientacao_service import OrientacaoService, get_orientacao_service

router = APIRouter(tags=["orientacoes"])


@router.post(
    "/orientacoes/sessoes",
    status_code=status.HTTP_201_CREATED,
)
async def registrar_sessao_orientacao(
    payload: SessaoOrientacaoPayload,
    session: Session = Depends(get_db_session),
    orientacao_service: OrientacaoService = Depends(get_orientacao_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_orientador: UserRecord = Depends(require_perfis(Perfil.ORIENTADOR)),
) -> SessaoOrientacaoResponse:
    return orientacao_service.registrar_sessao(
        session=session,
        current_user=current_orientador,
        payload=payload,
        audit_service=audit_service,
    )


@router.get(
    "/orientacoes/sessoes",
    status_code=status.HTTP_200_OK,
)
async def listar_sessoes_orientador(
    aluno_id: str = Query(...),
    session: Session = Depends(get_db_session),
    orientacao_service: OrientacaoService = Depends(get_orientacao_service),
    current_orientador: UserRecord = Depends(require_perfis(Perfil.ORIENTADOR)),
) -> list[SessaoOrientacaoResponse]:
    return orientacao_service.listar_sessoes_orientador(
        session=session,
        current_user=current_orientador,
        aluno_id=aluno_id,
    )


@router.get(
    "/tcc/me/sessoes",
    status_code=status.HTTP_200_OK,
)
async def listar_minhas_sessoes_orientacao(
    session: Session = Depends(get_db_session),
    orientacao_service: OrientacaoService = Depends(get_orientacao_service),
    current_aluno: UserRecord = Depends(require_perfis(Perfil.ALUNO)),
) -> list[SessaoOrientacaoResponse]:
    return orientacao_service.listar_minhas_sessoes(
        session=session,
        current_user=current_aluno,
    )
