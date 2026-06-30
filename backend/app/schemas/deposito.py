from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from backend.app.models.deposito import StatusDeposito, TipoDocumentoDeposito


class DocumentoDepositoResponse(BaseModel):
    id: str
    tipo_documento: TipoDocumentoDeposito
    nome_arquivo: str
    mime_type: str | None = None
    tamanho_bytes: int
    possui_preview: bool
    criado_em: datetime


class DepositoResponse(BaseModel):
    id: str | None = None
    tcc_id: str
    aluno_id: str
    aluno_nome: str
    titulo_tcc: str
    status: StatusDeposito
    versao_final_nome: str | None = None
    documentos: list[DocumentoDepositoResponse] = Field(default_factory=list)
    observacao_revisao: str | None = None
    submetido_em: datetime | None = None
    atualizado_em: datetime | None = None


class DepositoStatusUpdateRequest(BaseModel):
    status: StatusDeposito
    observacao_revisao: str | None = Field(default=None, max_length=1000)

    @field_validator("observacao_revisao")
    @classmethod
    def normalize_observacao(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
