from fastapi import FastAPI

from backend.app.api.router import api_router
from backend.app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.app_debug,
)
app.include_router(api_router)


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} online"}
