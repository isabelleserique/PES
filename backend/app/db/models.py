from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.models.banca import PapelBanca
from backend.app.models.deposito import StatusDeposito, TipoDocumentoDeposito
from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import AcaoEdicaoTCC, StatusTCC
from backend.app.models.user import Perfil, StatusCadastro

TIPO_TCC_ENUM = Enum(
    TipoTCC,
    name="TipoTCC",
    values_callable=lambda enum_class: [item.value for item in enum_class],
    validate_strings=True,
)

PAPEL_BANCA_ENUM = Enum(
    PapelBanca,
    name="PapelBanca",
    values_callable=lambda enum_class: [item.value for item in enum_class],
    validate_strings=True,
)

STATUS_DEPOSITO_ENUM = Enum(
    StatusDeposito,
    name="StatusDeposito",
    values_callable=lambda enum_class: [item.value for item in enum_class],
    validate_strings=True,
)

TIPO_DOCUMENTO_DEPOSITO_ENUM = Enum(
    TipoDocumentoDeposito,
    name="TipoDocumentoDeposito",
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
    email_prazos_orientandos: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notificacao_antecedencia_dias: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    email_notas_parciais: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_notas_finais: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    publicar_tcc_portal_publico: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    compartilhar_dados_terceiros: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    privacidade_atualizado_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    audit_logs: Mapped[list["AuditLogRecord"]] = relationship(back_populates="user")
    notificacoes_prazos: Mapped[list["NotificacaoPrazoRecord"]] = relationship(back_populates="aluno")
    membros_banca: Mapped[list["MembroBancaRecord"]] = relationship(back_populates="user")


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
    resumo: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    area_tematica: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    curso: Mapped[str] = mapped_column(String, default="Ciência da Computação", nullable=False, index=True)
    data_defesa: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    banca: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
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
    orientacao_sessoes: Mapped[list["OrientacaoSessaoRecord"]] = relationship(
        back_populates="tcc",
        cascade="all, delete-orphan",
    )
    apresentacoes_artigo: Mapped[list["ApresentacaoArtigoRecord"]] = relationship(
        back_populates="tcc",
        cascade="all, delete-orphan",
    )
    banca_defesa: Mapped[Optional["BancaRecord"]] = relationship(
        back_populates="tcc",
        uselist=False,
        cascade="all, delete-orphan",
    )
    deposito_final: Mapped[Optional["DepositoFinalRecord"]] = relationship(
        back_populates="tcc",
        uselist=False,
        cascade="all, delete-orphan",
    )
    notificacoes_prazos: Mapped[list["NotificacaoPrazoRecord"]] = relationship(
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


class OrientacaoSessaoRecord(Base):
    __tablename__ = "orientacao_sessoes"

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
    orientador_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_sessao: Mapped[date] = mapped_column(Date, nullable=False)
    resumo: Mapped[str] = mapped_column(String, nullable=False)
    proximos_passos: Mapped[str] = mapped_column(String, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    tcc: Mapped[TCCRecord] = relationship(back_populates="orientacao_sessoes")


class ApresentacaoArtigoRecord(Base):
    __tablename__ = "apresentacoes_artigo"

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
    data_apresentacao: Mapped[date] = mapped_column(Date, nullable=False)
    artigo_ja_aceito: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    tcc: Mapped[TCCRecord] = relationship(back_populates="apresentacoes_artigo")


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


class BancaRecord(Base):
    __tablename__ = "bancas"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tcc_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("tccs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    data_defesa: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    local: Mapped[str] = mapped_column(String, nullable=False)
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
    tcc: Mapped[TCCRecord] = relationship(back_populates="banca_defesa")
    membros: Mapped[list["MembroBancaRecord"]] = relationship(
        back_populates="banca",
        cascade="all, delete-orphan",
    )


class MembroBancaRecord(Base):
    __tablename__ = "membros_banca"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    banca_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("bancas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    nome: Mapped[str] = mapped_column(String, nullable=False)
    titulacao: Mapped[str] = mapped_column(String, nullable=False)
    instituicao: Mapped[str] = mapped_column(String, nullable=False)
    papel: Mapped[PapelBanca] = mapped_column(PAPEL_BANCA_ENUM, nullable=False)
    banca: Mapped[BancaRecord] = relationship(back_populates="membros")
    user: Mapped[Optional[UserRecord]] = relationship(back_populates="membros_banca")


class DepositoFinalRecord(Base):
    __tablename__ = "depositos_finais"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    tcc_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("tccs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status: Mapped[StatusDeposito] = mapped_column(
        STATUS_DEPOSITO_ENUM,
        nullable=False,
        default=StatusDeposito.AGUARDANDO_ENVIO,
        index=True,
    )
    observacao_revisao: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    submetido_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
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
    tcc: Mapped[TCCRecord] = relationship(back_populates="deposito_final")
    documentos: Mapped[list["DocumentoDepositoRecord"]] = relationship(
        back_populates="deposito",
        cascade="all, delete-orphan",
    )


class DocumentoDepositoRecord(Base):
    __tablename__ = "documentos_deposito"
    __table_args__ = (
        UniqueConstraint("deposito_id", "tipo_documento", name="uq_documento_deposito_tipo"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    deposito_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("depositos_finais.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo_documento: Mapped[TipoDocumentoDeposito] = mapped_column(TIPO_DOCUMENTO_DEPOSITO_ENUM, nullable=False)
    nome_original: Mapped[str] = mapped_column(String, nullable=False)
    caminho_original: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tamanho_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    caminho_preview_pdf: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )
    deposito: Mapped[DepositoFinalRecord] = relationship(back_populates="documentos")


class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    acao: Mapped[str] = mapped_column(String, nullable=False, index=True)
    entidade: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    descricao: Mapped[str] = mapped_column(String, nullable=False)
    dados: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    user: Mapped[Optional[UserRecord]] = relationship(back_populates="audit_logs")


class NotificacaoPrazoRecord(Base):
    __tablename__ = "notificacoes_prazos"
    __table_args__ = (
        UniqueConstraint("tcc_id", "prazo_id", "tipo_alerta", name="uq_notificacoes_prazos_tcc_prazo_tipo"),
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
    prazo_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("prazos_etapas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo_alerta: Mapped[str] = mapped_column(String, nullable=False, index=True)
    canal: Mapped[str] = mapped_column(String, default="EMAIL", nullable=False)
    enviado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    tcc: Mapped[TCCRecord] = relationship(back_populates="notificacoes_prazos")
    aluno: Mapped[UserRecord] = relationship(back_populates="notificacoes_prazos")
