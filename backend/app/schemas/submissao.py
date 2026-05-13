from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SubmissaoEntregavelResponse(BaseModel):
    id: str
    tipo_tcc: str
    etapa: str
    versao: int
    nome_arquivo: str
    data_submissao: datetime
    fora_do_prazo: bool
    foi_aceito: bool
    nome_comprovante: Optional[str] = None


class SubmissaoEntregavelCreateResponse(BaseModel):
    id: str
    tipo_tcc: str
    etapa: str
    versao: int
    mensagem: str
    nota_automatica: Optional[int] = None
