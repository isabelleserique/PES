from __future__ import annotations

from datetime import date, datetime
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
    ultima_versao: bool = False
    nome_comprovante: Optional[str] = None
    nota_automatica: Optional[int] = None


class SubmissaoEntregavelCreateResponse(BaseModel):
    id: str
    tipo_tcc: str
    etapa: str
    versao: int
    mensagem: str
    nota_automatica: Optional[int] = None


class SubmissaoHistoricoResponse(BaseModel):
    id: str
    aluno_id: str
    aluno_nome: str
    matricula: Optional[str] = None
    tcc_id: str
    titulo_tcc: str
    tipo_tcc: str
    etapa: str
    versao: int
    nome_arquivo: str
    data_submissao: datetime
    fora_do_prazo: bool
    foi_aceito: bool
    ultima_versao: bool = False
    nome_comprovante: Optional[str] = None
    nota_automatica: Optional[int] = None


class SubmissaoAtrasadaResponse(BaseModel):
    id: str
    aluno_id: str
    aluno_nome: str
    matricula: Optional[str] = None
    tcc_id: str
    titulo_tcc: str
    tipo_tcc: str
    etapa: str
    versao: int
    nome_arquivo: str
    data_limite: date
    data_submissao: datetime
    dias_atraso: int


class ApresentacaoArtigoPayload(BaseModel):
    data_apresentacao: date


class ApresentacaoArtigoResponse(BaseModel):
    id: str
    tcc_id: str
    data_apresentacao: date
    artigo_ja_aceito: bool
    criado_em: datetime
