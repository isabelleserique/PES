from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from backend.app.models.periodo import TipoTCC


class TccPublicoResponse(BaseModel):
    id: str
    titulo: str
    tipo_tcc: TipoTCC
    area_tematica: str | None = None
    curso: str
    aluno_nome: str
    orientador_nome: str
    data_defesa: date | None = None
    banca: list[str] = Field(default_factory=list)


class DocumentoTccPublicoResponse(BaseModel):
    id: str
    tipo: str
    nome_arquivo: str
    url_download: str
    url_preview: str | None = None


class TccPublicoDetalheResponse(TccPublicoResponse):
    resumo: str | None = None
    documentos: list[DocumentoTccPublicoResponse] = Field(default_factory=list)


class PublicStoredFile(BaseModel):
    path: str
    filename: str
    media_type: str
