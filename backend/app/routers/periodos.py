from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_active_coordenador, get_current_authenticated_user
from backend.app.db.models import UserRecord
from backend.app.db.session import get_db_session
from backend.app.schemas.periodo import (
    CronogramaPeriodoResponse,
    CreatePeriodoRequest,
    PeriodoResponse,
    UpdatePeriodoRequest,
)
from backend.app.services.periodo_service import PeriodoService, get_periodo_service

router = APIRouter(tags=["periodos"])


@router.post(
    "/periodos",
    status_code=status.HTTP_201_CREATED,
)
async def create_periodo(
    payload: CreatePeriodoRequest,
    session: Session = Depends(get_db_session),
    periodo_service: PeriodoService = Depends(get_periodo_service),
    current_coordenador: UserRecord = Depends(get_current_active_coordenador),
) -> PeriodoResponse:
    _ = current_coordenador
    return periodo_service.create_periodo(session=session, payload=payload)


@router.get(
    "/periodos",
    status_code=status.HTTP_200_OK,
)
async def list_periodos(
    session: Session = Depends(get_db_session),
    periodo_service: PeriodoService = Depends(get_periodo_service),
    current_coordenador: UserRecord = Depends(get_current_active_coordenador),
) -> list[PeriodoResponse]:
    _ = current_coordenador
    return periodo_service.list_periodos(session=session)


@router.get(
    "/periodos/ativo",
    status_code=status.HTTP_200_OK,
)
async def get_active_periodo(
    session: Session = Depends(get_db_session),
    periodo_service: PeriodoService = Depends(get_periodo_service),
    current_user: UserRecord = Depends(get_current_authenticated_user),
) -> PeriodoResponse:
    _ = current_user
    return periodo_service.get_active_periodo(session=session)


@router.get(
    "/periodos/ativo/cronograma",
    status_code=status.HTTP_200_OK,
)
async def get_active_periodo_cronograma(
    orientando_id: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
    periodo_service: PeriodoService = Depends(get_periodo_service),
    current_user: UserRecord = Depends(get_current_authenticated_user),
) -> CronogramaPeriodoResponse:
    return periodo_service.get_cronograma(
        session=session,
        current_user=current_user,
        orientando_id=orientando_id,
    )


@router.get(
    "/periodos/{periodo_id}",
    status_code=status.HTTP_200_OK,
)
async def get_periodo_by_id(
    periodo_id: str,
    session: Session = Depends(get_db_session),
    periodo_service: PeriodoService = Depends(get_periodo_service),
    current_coordenador: UserRecord = Depends(get_current_active_coordenador),
) -> PeriodoResponse:
    _ = current_coordenador
    return periodo_service.get_periodo_by_id(session=session, periodo_id=periodo_id)


@router.patch(
    "/periodos/{periodo_id}",
    status_code=status.HTTP_200_OK,
)
async def update_periodo(
    periodo_id: str,
    payload: UpdatePeriodoRequest,
    session: Session = Depends(get_db_session),
    periodo_service: PeriodoService = Depends(get_periodo_service),
    current_coordenador: UserRecord = Depends(get_current_active_coordenador),
) -> PeriodoResponse:
    _ = current_coordenador
    return periodo_service.update_periodo(
        session=session,
        periodo_id=periodo_id,
        payload=payload,
    )
