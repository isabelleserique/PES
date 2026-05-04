from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import StatusTCC


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
    criado_em: datetime
    atualizado_em: datetime
