from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class SessaoOrientacaoPayload(BaseModel):
    aluno_id: str = Field(min_length=1)
    data_sessao: date
    resumo: str = Field(min_length=10, max_length=4000)
    proximos_passos: str = Field(min_length=10, max_length=4000)

    @field_validator("aluno_id", "resumo", "proximos_passos")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Campo obrigatorio.")
        return normalized


class SessaoOrientacaoResponse(BaseModel):
    id: str
    tcc_id: str
    aluno_id: str
    aluno_nome: str
    orientador_id: str
    orientador_nome: str
    data_sessao: date
    resumo: str
    proximos_passos: str
    criado_em: datetime
