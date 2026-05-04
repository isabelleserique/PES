from fastapi import APIRouter, Depends, status

from backend.app.api.deps import get_current_authenticated_user
from backend.app.db.models import UserRecord
from backend.app.services.period_service import PeriodService, get_period_service

router = APIRouter(prefix="/periodos", tags=["periodos"])

@router.get(
    "/ativo/prazos",
    status_code=status.HTTP_200_OK,
)
async def get_prazos_periodo_ativo(
    period_service: PeriodService = Depends(get_period_service),
    current_user: UserRecord = Depends(get_current_authenticated_user),
):
    return period_service.get_prazos_visiveis(current_user=current_user)