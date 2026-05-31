from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from backend.app.api.router import api_router
from backend.app.core.config import get_settings
from backend.app.middleware.authentication import jwt_authentication_middleware

from apscheduler.schedulers.background import BackgroundScheduler
from backend.app.services.backup_service import backup_service

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.app_debug,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url.rstrip("/")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(jwt_authentication_middleware)
app.include_router(api_router)


@app.get("/", tags=["meta"], include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url=app.docs_url or "/docs")

scheduler = BackgroundScheduler()

def start_backup_scheduler():
    scheduler.add_job(
        backup_service.run_backup,
        "cron",
        hour=2,
        minute=0,
    )
    scheduler.start()

@app.on_event("startup")
def startup_event():
    start_backup_scheduler()