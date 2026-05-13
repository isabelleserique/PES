from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import AcaoEdicaoTCC, StatusTCC
from backend.app.models.user import Perfil, StatusCadastro

TIPO_TCC_ENUM = Enum(
    TipoTCC,
    name="TipoTCC",
    values_callable=lambda enum_class: [item.value for item in enum_class],
    validate_strings=True,
)


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
    tccs: Mapped[list["TCCRecord"]] = relationship(
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
    tipo_tcc: Mapped[TipoTCC] = mapped_column(TIPO_TCC_ENUM, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    periodo: Mapped[PeriodoLetivoRecord] = relationship(back_populates="prazos")


class TCCRecord(Base):
    __tablename__ = "tccs"
    __table_args__ = (
        UniqueConstraint("aluno_id", "periodo_id", name="uq_tcc_aluno_periodo"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    tipo_tcc: Mapped[TipoTCC] = mapped_column(TIPO_TCC_ENUM, nullable=False)
    aluno_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    orientador_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    coorientador_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    periodo_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("periodos_letivos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[StatusTCC] = mapped_column(
        Enum(StatusTCC, name="StatusTCC"),
        nullable=False,
        default=StatusTCC.AGUARDANDO_ACEITE,
    )
    prazo_excedido: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    observacao_orientador: Mapped[Optional[str]] = mapped_column(String, nullable=True)
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
    periodo: Mapped[PeriodoLetivoRecord] = relationship(back_populates="tccs")
    logs: Mapped[list["TCCEditLogRecord"]] = relationship(
        back_populates="tcc",
        cascade="all, delete-orphan",
    )
    submissoes_entregaveis: Mapped[list["SubmissaoEntregavelRecord"]] = relationship(
        back_populates="tcc",
        cascade="all, delete-orphan",
    )


class SubmissaoEntregavelRecord(Base):
    __tablename__ = "submissoes_entregaveis"
    __table_args__ = (
        UniqueConstraint("tcc_id", "etapa", "versao", name="uq_submissoes_entregaveis_tcc_etapa_versao"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tcc_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("tccs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    aluno_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo_tcc: Mapped[TipoTCC] = mapped_column(TIPO_TCC_ENUM, nullable=False)
    etapa: Mapped[str] = mapped_column(String, nullable=False)
    versao: Mapped[int] = mapped_column(Integer, nullable=False)
    nome_arquivo: Mapped[str] = mapped_column(String, nullable=False)
    caminho_arquivo: Mapped[str] = mapped_column(String, nullable=False)
    tipo_conteudo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tamanho_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    foi_aceito: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    nome_comprovante: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    caminho_comprovante: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tipo_conteudo_comprovante: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tamanho_comprovante_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fora_do_prazo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    nota_automatica: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    tcc: Mapped[TCCRecord] = relationship(back_populates="submissoes_entregaveis")


class TCCEditLogRecord(Base):
    __tablename__ = "tcc_edit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tcc_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("tccs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    acao: Mapped[AcaoEdicaoTCC] = mapped_column(
        Enum(AcaoEdicaoTCC, name="AcaoEdicaoTCC"),
        nullable=False,
    )
    observacao: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    dados_anteriores: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    dados_novos: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    tcc: Mapped[TCCRecord] = relationship(back_populates="logs")


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
