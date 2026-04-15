from fastapi import APIRouter

from backend.app.core.config import get_settings

router = APIRouter()


@router.get("/health")
async def get_health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }
