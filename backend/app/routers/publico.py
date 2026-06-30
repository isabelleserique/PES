from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.db.session import get_db_session
from backend.app.schemas.publico import TccPublicoDetalheResponse, TccPublicoResponse
from backend.app.services.publico_service import PublicoService, get_publico_service

router = APIRouter(prefix="/public", tags=["public"])


@router.get(
    "/tcc",
    status_code=status.HTTP_200_OK,
)
async def buscar_tccs_publicos(
    area_tematica: str | None = Query(default=None),
    curso: str | None = Query(default=None),
    aluno: str | None = Query(default=None),
    titulo: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
    publico_service: PublicoService = Depends(get_publico_service),
) -> list[TccPublicoResponse]:
    return publico_service.buscar_tccs(
        session=session,
        area_tematica=area_tematica,
        curso=curso,
        aluno=aluno,
        titulo=titulo,
    )


@router.get(
    "/tcc/{tcc_id}",
    status_code=status.HTTP_200_OK,
)
async def get_tcc_publico_detalhe(
    tcc_id: str,
    session: Session = Depends(get_db_session),
    publico_service: PublicoService = Depends(get_publico_service),
) -> TccPublicoDetalheResponse:
    return publico_service.get_tcc_detalhe(session=session, tcc_id=tcc_id)


@router.get(
    "/tcc/{tcc_id}/documentos/{submissao_id}/arquivo",
    status_code=status.HTTP_200_OK,
)
async def get_documento_tcc_publico(
    tcc_id: str,
    submissao_id: str,
    download: bool = Query(default=False),
    session: Session = Depends(get_db_session),
    publico_service: PublicoService = Depends(get_publico_service),
) -> FileResponse:
    arquivo = publico_service.get_documento_publico(
        session=session,
        tcc_id=tcc_id,
        submissao_id=submissao_id,
        download=download,
    )
    return FileResponse(
        path=arquivo.path,
        media_type=arquivo.media_type,
        filename=arquivo.filename,
        content_disposition_type="attachment" if download else "inline",
    )
