from pydantic import BaseModel
from datetime import date


class PeriodoResumo(BaseModel):
    id: str
    nome: str
    data_inicio: date
    data_fim: date


class DashboardAlunos(BaseModel):
    total: int
    por_tipo_tcc: dict
    sem_orientador: int


class DashboardStatusTCC(BaseModel):
    artigos_aceitos: int


class DashboardPrazos(BaseModel):
    vencidos: int


class DashboardEntregas(BaseModel):
    pendentes: int

class DashboardAlunoItem(BaseModel):
    aluno_id: str
    nome: str
    tipo_tcc: str
    tem_orientador: bool
    status_tcc: str
    prazos_vencidos: int
    entregas_pendentes: int

class PeriodoDashboardResponse(BaseModel):
    periodo: PeriodoResumo
    alunos: DashboardAlunos
    status_tcc: DashboardStatusTCC
    prazos: DashboardPrazos
    entregas: DashboardEntregas

    alunos_detalhados: list[DashboardAlunoItem]