from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.models.banca import PapelBanca


class MembroBancaRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=255)
    titulacao: str = Field(min_length=2, max_length=255)
    instituicao: str = Field(min_length=2, max_length=255)
    papel: PapelBanca = PapelBanca.AVALIADOR_INTERNO

    @field_validator("nome", "titulacao", "instituicao")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return " ".join(value.strip().split())


class BancaRequest(BaseModel):
    aluno_id: str | None = Field(default=None, min_length=1, max_length=255)
    data_defesa: datetime
    local: str = Field(min_length=2, max_length=255)
    membros: list[MembroBancaRequest] = Field(min_length=2, max_length=8)

    @field_validator("local")
    @classmethod
    def normalize_local(cls, value: str) -> str:
        return " ".join(value.strip().split())

    @model_validator(mode="after")
    def validate_membros(self) -> "BancaRequest":
        papeis = [membro.papel for membro in self.membros]
        if len(set(papeis)) != len(papeis):
            raise ValueError("Nao informe papeis duplicados na banca.")
        if PapelBanca.AVALIADOR_INTERNO not in papeis or PapelBanca.AVALIADOR_EXTERNO not in papeis:
            raise ValueError("Informe ao menos um avaliador interno e um avaliador externo.")
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
    aluno_id: str
    aluno_nome: str
    data_defesa: datetime
    local: str
    membros: list[MembroBancaResponse]
    criado_em: datetime
    atualizado_em: datetime
