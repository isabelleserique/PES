from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from backend.app.models.user import Perfil, StatusCadastro

from backend.app.models.tcc import TipoTCC, StatusTCC

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


class PasswordResetTokenRecord(Base):
    __tablename__ = "password_reset_tokens"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    usado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )


class TCCRecord(Base):
    __tablename__ = "tccs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    titulo: Mapped[str] = mapped_column(String, nullable=False)

    tipo: Mapped[TipoTCC] = mapped_column(Enum(TipoTCC), nullable=False)

    aluno_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    orientador_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    coorientador_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"), nullable=True)

    periodo: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[StatusTCC] = mapped_column(
        Enum(StatusTCC),
        default=StatusTCC.AGUARDANDO_ACEITE,
        nullable=False,
    )

    prazo_excedido: Mapped[bool] = mapped_column(Boolean, default=False)
    

    criado_em: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        nullable=False
    )

    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )