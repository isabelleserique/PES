from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.api.deps import require_perfis
from backend.app.db.models import UserRecord
from backend.app.db.session import get_db_session
from backend.app.models.user import Perfil
from backend.app.schemas.submissao import (
    SubmissaoEntregavelCreateResponse,
    SubmissaoEntregavelResponse,
    SubmissaoHistoricoResponse,
)
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
    "/entregaveis/{submissao_id}/arquivo",
    status_code=status.HTTP_200_OK,
)
async def visualizar_arquivo_entregavel(
    submissao_id: str,
    session: Session = Depends(get_db_session),
    submissao_service: SubmissaoService = Depends(get_submissao_service),
    current_user: UserRecord = Depends(require_perfis(Perfil.ALUNO, Perfil.ORIENTADOR, Perfil.COORDENADOR)),
) -> FileResponse:
    arquivo = submissao_service.get_arquivo_submissao(
        session=session,
        current_user=current_user,
        submissao_id=submissao_id,
        comprovante=False,
    )
    return FileResponse(
        path=arquivo.path,
        media_type=arquivo.media_type,
        filename=arquivo.filename,
        content_disposition_type="inline",
    )


@router.get(
    "/entregaveis/{submissao_id}/comprovante",
    status_code=status.HTTP_200_OK,
)
async def visualizar_comprovante_entregavel(
    submissao_id: str,
    session: Session = Depends(get_db_session),
    submissao_service: SubmissaoService = Depends(get_submissao_service),
    current_user: UserRecord = Depends(require_perfis(Perfil.ALUNO, Perfil.ORIENTADOR, Perfil.COORDENADOR)),
) -> FileResponse:
    comprovante = submissao_service.get_arquivo_submissao(
        session=session,
        current_user=current_user,
        submissao_id=submissao_id,
        comprovante=True,
    )
    return FileResponse(
        path=comprovante.path,
        media_type=comprovante.media_type,
        filename=comprovante.filename,
        content_disposition_type="inline",
    )


@router.get(
    "/historico",
    status_code=status.HTTP_200_OK,
)
async def listar_historico_submissoes(
    session: Session = Depends(get_db_session),
    submissao_service: SubmissaoService = Depends(get_submissao_service),
    current_coordenador: UserRecord = Depends(require_perfis(Perfil.COORDENADOR)),
) -> list[SubmissaoHistoricoResponse]:
    return submissao_service.listar_historico_coordenador(
        session=session,
        current_user=current_coordenador,
    )


@router.get(
    "/coordenador",
    status_code=status.HTTP_200_OK,
)
async def listar_submissoes_coordenador(
    session: Session = Depends(get_db_session),
    submissao_service: SubmissaoService = Depends(get_submissao_service),
    current_coordenador: UserRecord = Depends(require_perfis(Perfil.COORDENADOR)),
) -> list[SubmissaoHistoricoResponse]:
    return submissao_service.listar_historico_coordenador(
        session=session,
        current_user=current_coordenador,
    )


@router.get(
    "/orientador",
    status_code=status.HTTP_200_OK,
)
async def listar_submissoes_orientador(
    session: Session = Depends(get_db_session),
    submissao_service: SubmissaoService = Depends(get_submissao_service),
    current_orientador: UserRecord = Depends(require_perfis(Perfil.ORIENTADOR)),
) -> list[SubmissaoHistoricoResponse]:
    return submissao_service.listar_historico_orientador(
        session=session,
        current_user=current_orientador,
    )
