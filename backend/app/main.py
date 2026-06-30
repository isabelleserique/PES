import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from backend.app.api.router import api_router
from backend.app.core.config import get_settings
from backend.app.middleware.authentication import jwt_authentication_middleware
from backend.app.services.backup_service import run_daily_backup_loop
from backend.app.services.notificacao_service import run_deadline_notification_loop

settings = get_settings()
backup_task: asyncio.Task | None = None
notification_task: asyncio.Task | None = None


def get_allowed_origins() -> list[str]:
    origins = settings.cors_origins or settings.frontend_url
    return [
        origin.strip().rstrip("/")
        for origin in origins.split(",")
        if origin.strip()
    ]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global backup_task, notification_task
    backup_task = asyncio.create_task(run_daily_backup_loop())
    notification_task = asyncio.create_task(run_deadline_notification_loop())
    try:
        yield
    finally:
        for task in (backup_task, notification_task):
            if task is None:
                continue
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        backup_task = None
        notification_task = None


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.app_debug,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(jwt_authentication_middleware)
app.include_router(api_router)


@app.get("/", tags=["meta"], include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url=app.docs_url or "/docs")
