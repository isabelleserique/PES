from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import StatusTCC


class TCCWriteRequest(BaseModel):
    titulo: str = Field(min_length=3, max_length=255)
    tipo_tcc: TipoTCC
    orientador_id: str = Field(min_length=1, max_length=255)
    coorientador_id: Optional[str] = Field(default=None, max_length=255)
    resumo: Optional[str] = Field(default=None, max_length=4000)
    area_tematica: Optional[str] = Field(default=None, max_length=255)
    curso: Optional[str] = Field(default=None, max_length=255)
    data_defesa: Optional[date] = None
    banca: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("titulo", "orientador_id", "coorientador_id", "resumo", "area_tematica", "curso")
    @classmethod
    def normalize_text_fields(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            return None
        return normalized

    @field_validator("banca")
    @classmethod
    def normalize_banca(cls, value: list[str]) -> list[str]:
        normalized = []
        for membro in value:
            nome = membro.strip()
            if nome:
                normalized.append(nome)
        return normalized

    @model_validator(mode="after")
    def validate_tcc_submission(self) -> "TCCWriteRequest":
        if self.tipo_tcc == TipoTCC.TODOS:
            raise ValueError("Selecione um tipo de TCC valido para o aluno.")
        if self.coorientador_id and self.coorientador_id == self.orientador_id:
            raise ValueError("Orientador e coorientador nao podem ser a mesma pessoa.")
        return self


class OrientadorDisponivelResponse(BaseModel):
    id: str
    nome_completo: str
    email: str


class TCCResponse(BaseModel):
    id: str
    titulo: str
    tipo_tcc: TipoTCC
    orientador_id: str
    orientador_nome: str
    coorientador_id: Optional[str] = None
    coorientador_nome: Optional[str] = None
    periodo_id: str
    periodo_nome: str
    status: StatusTCC
    prazo_excedido: bool
    alerta_prazo: Optional[str] = None
    observacao_orientador: Optional[str] = None
    resumo: Optional[str] = None
    area_tematica: Optional[str] = None
    curso: str
    data_defesa: Optional[date] = None
    banca: list[str] = Field(default_factory=list)
    criado_em: datetime
    atualizado_em: datetime


class OrientationRequestResponse(BaseModel):
    tcc_id: str
    aluno_id: str
    aluno_nome: str
    aluno_email: str
    matricula: Optional[str] = None
    titulo: str
    tipo_tcc: TipoTCC
    status: StatusTCC
    prazo_excedido: bool
    alerta_submissao_prazo: Optional[str] = None
    prazo_aceite: Optional[date] = None
    acao_fora_do_prazo: bool
    alerta_acao_prazo: Optional[str] = None
    criado_em: datetime


class OrientationDecisionRequest(BaseModel):
    acao: str = Field(min_length=1, max_length=20)
    observacao: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("acao")
    @classmethod
    def normalize_action(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"ACEITAR", "RECUSAR"}:
            raise ValueError("Acao invalida. Use ACEITAR ou RECUSAR.")
        return normalized

    @field_validator("observacao")
    @classmethod
    def normalize_observacao(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            return None
        return normalized

    @model_validator(mode="after")
    def validate_observacao(self) -> "OrientationDecisionRequest":
        if self.acao == "RECUSAR" and not self.observacao:
            raise ValueError("Observacao e obrigatoria ao recusar a orientacao.")
        return self


class OrientationDecisionResponse(BaseModel):
    tcc_id: str
    aluno_id: str
    aluno_nome: str
    status: StatusTCC
    observacao_orientador: Optional[str] = None
    acao_fora_do_prazo: bool
    alerta_acao_prazo: Optional[str] = None
