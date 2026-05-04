from __future__ import annotations

from datetime import datetime
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.models.periodo import TipoTCC
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


class PeriodoLetivoRecord(Base):
    __tablename__ = "periodos_letivos"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    nome: Mapped[str] = mapped_column(String, nullable=False, index=True)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_fim: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    prazos: Mapped[list["PrazoEtapaRecord"]] = relationship(
        back_populates="periodo",
        cascade="all, delete-orphan",
    )


class PrazoEtapaRecord(Base):
    __tablename__ = "prazos_etapas"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    periodo_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("periodos_letivos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nome_etapa: Mapped[str] = mapped_column(String, nullable=False)
    data_limite: Mapped[date] = mapped_column(Date, nullable=False)
    tipo_tcc: Mapped[TipoTCC] = mapped_column(Enum(TipoTCC, name="TipoTCC"), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    periodo: Mapped[PeriodoLetivoRecord] = relationship(back_populates="prazos")


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