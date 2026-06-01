from fastapi import APIRouter

from backend.app.routers.auth import router as auth_router
from backend.app.routers.health import router as health_router
from backend.app.routers.periodos import router as periodos_router
from backend.app.routers.submissoes import router as submissoes_router
from backend.app.routers.tcc import router as tcc_router
from backend.app.routers.users import router as users_router
from backend.app.routers.audit import router as audit_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
api_router.include_router(periodos_router)
api_router.include_router(submissoes_router)
api_router.include_router(tcc_router)
api_router.include_router(users_router)
api_router.include_router(audit_router)
