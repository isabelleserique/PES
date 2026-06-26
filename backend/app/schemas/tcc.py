from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import StatusTCC
from backend.app.models.banca import PapelBanca


class TCCWriteRequest(BaseModel):
    titulo: str = Field(min_length=3, max_length=255)
    tipo_tcc: TipoTCC
    orientador_id: str = Field(min_length=1, max_length=255)
    coorientador_id: Optional[str] = Field(default=None, max_length=255)

    @field_validator("titulo", "orientador_id", "coorientador_id")
    @classmethod
    def normalize_text_fields(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            return None
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

class MembroBancaRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=255)
    titulacao: str = Field(min_length=2, max_length=255)
    instituicao: str = Field(min_length=2, max_length=255)
    papel: PapelBanca

    @field_validator("nome", "titulacao", "instituicao")
    @classmethod
    def normalize(cls, value: str) -> str:
        return value.strip()


class BancaRequest(BaseModel):
    data_defesa: datetime
    local: str = Field(min_length=2, max_length=255)
    membros: list[MembroBancaRequest]

    @field_validator("local")
    @classmethod
    def normalize_local(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_membros(self) -> "BancaRequest":
        if len(self.membros) != 3:
            raise ValueError(
                "A banca deve possuir exatamente três membros informados (avaliador interno, avaliador externo e suplente)."
            )

        papeis = [m.papel for m in self.membros]

        required = {
            PapelBanca.AVALIADOR_INTERNO,
            PapelBanca.AVALIADOR_EXTERNO,
            PapelBanca.SUPLENTE,
        }

        if set(papeis) != required:
            raise ValueError(
                "A banca deve conter exatamente um avaliador interno, um avaliador externo e um suplente."
            )

        return self


class MembroBancaResponse(BaseModel):
    id: str
    nome: str
    titulacao: str
    instituicao: str
    papel: PapelBanca


class BancaResponse(BaseModel):
    id: str
    tcc_id: str
    data_defesa: datetime
    local: str
    membros: list[MembroBancaResponse]