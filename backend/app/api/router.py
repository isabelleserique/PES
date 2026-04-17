from fastapi import APIRouter

from backend.app.routers.auth import router as auth_router
from backend.app.routers.health import router as health_router
from backend.app.routers.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(users_router)
