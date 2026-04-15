from __future__ import annotations

from typing import Annotated
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import UserRecord
from backend.app.db.session import get_db_session
from backend.app.models.user import Perfil, StatusCadastro


async def get_current_active_coordenador(
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    session: Session = Depends(get_db_session),
) -> UserRecord:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificacao do usuario coordenador nao informada.",
        )

    coordenador = session.scalar(select(UserRecord).where(UserRecord.id == x_user_id))
    if (
        coordenador is None
        or coordenador.perfil != Perfil.COORDENADOR
        or coordenador.status != StatusCadastro.ATIVO
        or coordenador.ativo is not True
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a coordenadores ativos.",
        )

    return coordenador
