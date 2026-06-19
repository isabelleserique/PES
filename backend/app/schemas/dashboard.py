from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class DashboardPeriodoResumo(BaseModel):
    id: str
    nome: str
    data_inicio: date
    data_fim: date


class DashboardTipoTccResumo(BaseModel):
    monografia: int = 0
    artigo: int = 0
    relatorio_estagio: int = 0
    sem_tcc: int = 0


class DashboardDepositoBiblioteca(BaseModel):
    depositados: int = 0
    pendentes: int = 0
    status: str = "derivado_das_submissoes_finais"


class DashboardAlunosResumo(BaseModel):
    total: int = 0
    por_tipo: DashboardTipoTccResumo = Field(default_factory=DashboardTipoTccResumo)
    sem_orientador_aceito: int = 0
    com_prazo_vencido_sem_entrega: int = 0
    deposito_biblioteca: DashboardDepositoBiblioteca = Field(default_factory=DashboardDepositoBiblioteca)


class DashboardAlunoDetalhe(BaseModel):
    aluno_id: str
    nome: str
    matricula: str | None = None
    titulo_tcc: str | None = None
    tipo_tcc: str | None = None
    status_tcc: str
    orientador_nome: str | None = None
    sem_orientador_aceito: bool
    prazos_vencidos_sem_entrega: int
    entregas_pendentes: int
    deposito_biblioteca: str


class PeriodoDashboardResponse(BaseModel):
    periodo: DashboardPeriodoResumo
    alunos: DashboardAlunosResumo
    alunos_detalhados: list[DashboardAlunoDetalhe] = Field(default_factory=list)
