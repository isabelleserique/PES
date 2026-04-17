from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import api_router
from backend.app.core.config import get_settings
from backend.app.middleware.authentication import jwt_authentication_middleware

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


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} online"}
