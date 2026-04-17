from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse

from backend.app.core.config import get_settings
from backend.app.core.security import ExpiredTokenError, InvalidTokenError, decode_access_token


async def jwt_authentication_middleware(request: Request, call_next):
    settings = get_settings()
    request.state.auth_payload = None

    authorization = request.headers.get("Authorization")
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token invalido."},
            )

        try:
            request.state.auth_payload = decode_access_token(
                token=token,
                secret_key=settings.jwt_secret,
                algorithm=settings.jwt_algorithm,
            )
        except ExpiredTokenError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token expirado."},
            )
        except InvalidTokenError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token invalido."},
            )

    return await call_next(request)
