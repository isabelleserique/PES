from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from backend.app.models.user import Perfil, StatusCadastro


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    nome_completo: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String, nullable=False)
    perfil: Mapped[Perfil] = mapped_column(Enum(Perfil, name="Perfil"), nullable=False)
    matricula: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[StatusCadastro] = mapped_column(
        Enum(StatusCadastro, name="UserStatus"),
        nullable=False,
        default=StatusCadastro.ATIVO,
    )
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    blocked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
