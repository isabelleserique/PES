from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.deps import require_perfis
from backend.app.db.models import UserRecord
from backend.app.db.session import get_db_session
from backend.app.models.user import Perfil
from backend.app.schemas.submissao import SubmissaoEntregavelCreateResponse, SubmissaoEntregavelResponse
from backend.app.services.submissao_service import SubmissaoService, get_submissao_service

router = APIRouter(prefix="/submissoes", tags=["submissoes"])


@router.get(
    "/entregaveis",
    status_code=status.HTTP_200_OK,
)
async def listar_submissoes_entregaveis(
    session: Session = Depends(get_db_session),
    submissao_service: SubmissaoService = Depends(get_submissao_service),
    current_aluno: UserRecord = Depends(require_perfis(Perfil.ALUNO)),
) -> list[SubmissaoEntregavelResponse]:
    return submissao_service.listar_entregaveis(session=session, current_user=current_aluno)


@router.post(
    "/entregaveis",
    status_code=status.HTTP_201_CREATED,
)
async def submeter_entregavel(
    arquivo: UploadFile = File(...),
    etapa: str | None = Form(None),
    foi_aceito: bool = Form(False),
    comprovante: UploadFile | None = File(None),
    session: Session = Depends(get_db_session),
    submissao_service: SubmissaoService = Depends(get_submissao_service),
    current_aluno: UserRecord = Depends(require_perfis(Perfil.ALUNO)),
) -> SubmissaoEntregavelCreateResponse:
    return await submissao_service.submeter_entregavel(
        session=session,
        current_user=current_aluno,
        etapa=etapa,
        arquivo=arquivo,
        foi_aceito=foi_aceito,
        comprovante=comprovante,
    )

@router.get(
    "/orientador",
    status_code=status.HTTP_200_OK,
)
async def listar_submissoes_orientador(
    session: Session = Depends(get_db_session),
    submissao_service: SubmissaoService = Depends(get_submissao_service),
    current_orientador: UserRecord = Depends(require_perfis(Perfil.ORIENTADOR)),
):
    return submissao_service.listar_submissoes_orientador(
        session=session,
        current_user=current_orientador,
    )

@router.get(
    "/coordenador",
    status_code=status.HTTP_200_OK,
)
async def listar_submissoes_coordenador(
    session: Session = Depends(get_db_session),
    submissao_service: SubmissaoService = Depends(get_submissao_service),
    current_user: UserRecord = Depends(require_perfis(Perfil.COORDENADOR)),
):
    return submissao_service.listar_submissoes_coordenador(
        session=session,
        current_user=current_user,
    )