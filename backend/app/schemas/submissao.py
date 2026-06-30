from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


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
    nota_orientador: Optional[float] = None
    nota_final: Optional[float] = None
    status_avaliacao: str = "AGUARDANDO"
    avaliado_por_id: Optional[str] = None
    avaliado_por_nome: Optional[str] = None
    avaliado_em: Optional[datetime] = None


class SubmissaoEntregavelCreateResponse(BaseModel):
    id: str
    tipo_tcc: str
    etapa: str
    versao: int
    mensagem: str
    nota_automatica: Optional[int] = None
    nota_final: Optional[float] = None
    status_avaliacao: str = "AGUARDANDO"


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
    nota_orientador: Optional[float] = None
    nota_final: Optional[float] = None
    status_avaliacao: str = "AGUARDANDO"
    avaliado_por_id: Optional[str] = None
    avaliado_por_nome: Optional[str] = None
    avaliado_em: Optional[datetime] = None


class SubmissaoAvaliacaoRequest(BaseModel):
    nota: float = Field(ge=0, le=10)


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
    tipo_veiculo: Optional[str] = None
    veiculo_publicacao: Optional[str] = None
    local_apresentacao: Optional[str] = None
    observacoes: Optional[str] = None


class ApresentacaoArtigoResponse(BaseModel):
    id: str
    tcc_id: str
    submissao_id: Optional[str] = None
    data_apresentacao: date
    tipo_veiculo: Optional[str] = None
    veiculo_publicacao: Optional[str] = None
    local_apresentacao: Optional[str] = None
    observacoes: Optional[str] = None
    artigo_ja_aceito: bool
    criado_em: datetime
