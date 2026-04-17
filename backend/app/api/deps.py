from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import UserRecord
from backend.app.db.session import get_db_session
from backend.app.models.user import Perfil, StatusCadastro
from backend.app.schemas.auth import AccessTokenPayload


async def get_access_token_payload(request: Request) -> AccessTokenPayload:
    raw_payload = getattr(request.state, "auth_payload", None)
    if raw_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso nao informado.",
        )

    try:
        return AccessTokenPayload.model_validate(raw_payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido.",
        ) from exc


async def get_current_authenticated_user(
    token_payload: AccessTokenPayload = Depends(get_access_token_payload),
    session: Session = Depends(get_db_session),
) -> UserRecord:
    user = session.scalar(select(UserRecord).where(UserRecord.id == token_payload.user_id))
    if user is None or user.perfil != token_payload.perfil:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido.",
        )

    if user.status != StatusCadastro.ATIVO or user.ativo is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario autenticado nao esta ativo.",
        )

    return user


def require_perfis(*allowed_profiles: Perfil) -> Callable[..., UserRecord]:
    async def dependency(
        token_payload: AccessTokenPayload = Depends(get_access_token_payload),
        current_user: UserRecord = Depends(get_current_authenticated_user),
    ) -> UserRecord:
        if token_payload.perfil not in allowed_profiles or current_user.perfil not in allowed_profiles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Perfil sem permissao para acessar este recurso.",
            )

        return current_user

    return dependency


async def get_current_active_coordenador(
    current_user: UserRecord = Depends(require_perfis(Perfil.COORDENADOR)),
) -> UserRecord:
    return current_user
