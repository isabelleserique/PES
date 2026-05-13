from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.app.models.periodo import TipoTCC
from backend.app.models.tcc import StatusTCC
from backend.app.models.user import Perfil


class PrazoPayload(BaseModel):
    nome_etapa: str = Field(min_length=1, max_length=255)
    data_limite: date
    tipo_tcc: TipoTCC

    @field_validator("nome_etapa")
    @classmethod
    def normalize_nome_etapa(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Campo obrigatorio.")
        return normalized


class PeriodoWriteRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    data_inicio: date
    data_fim: date
    ativo: bool = False
    prazos: list[PrazoPayload] = Field(default_factory=list)

    @field_validator("nome")
    @classmethod
    def normalize_nome(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Campo obrigatorio.")
        return normalized

    @model_validator(mode="after")
    def validate_periodo(self) -> "PeriodoWriteRequest":
        if self.data_inicio >= self.data_fim:
            raise ValueError("A data de inicio deve ser anterior a data de fim.")

        seen: set[tuple[str, TipoTCC]] = set()
        for prazo in self.prazos:
            if not self.data_inicio <= prazo.data_limite <= self.data_fim:
                raise ValueError("Todos os prazos devem estar entre a data de inicio e a data de fim do periodo.")

            key = (prazo.nome_etapa.casefold(), prazo.tipo_tcc)
            if key in seen:
                raise ValueError("Nao e permitido cadastrar prazos duplicados para a mesma etapa e tipo de TCC.")
            seen.add(key)

        return self


class CreatePeriodoRequest(PeriodoWriteRequest):
    pass


class UpdatePeriodoRequest(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=100)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    ativo: Optional[bool] = None
    prazos: Optional[list[PrazoPayload]] = None

    @field_validator("nome")
    @classmethod
    def normalize_nome(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            raise ValueError("Campo obrigatorio.")
        return normalized

    @model_validator(mode="after")
    def validate_has_changes(self) -> "UpdatePeriodoRequest":
        if all(value is None for value in (self.nome, self.data_inicio, self.data_fim, self.ativo, self.prazos)):
            raise ValueError("Informe ao menos um campo para atualizacao.")
        return self


class PrazoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome_etapa: str
    data_limite: date
    tipo_tcc: TipoTCC


class PeriodoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome: str
    data_inicio: date
    data_fim: date
    ativo: bool
    prazos: list[PrazoResponse]


class PeriodoResumoResponse(BaseModel):
    id: str
    nome: str
    data_inicio: date
    data_fim: date
    ativo: bool


class CronogramaPrazoResponse(BaseModel):
    id: str
    nome_etapa: str
    data_limite: date
    tipo_tcc: TipoTCC
    dias_restantes: int
    status: str
    cor: str
    mensagem: str
    atrasado: bool


class CronogramaAlunoResponse(BaseModel):
    aluno_id: str
    titulo_tcc: Optional[str] = None
    tipo_tcc: Optional[TipoTCC] = None
    status_tcc: Optional[StatusTCC] = None
    prazo_excedido: bool = False
    alerta_prazo: Optional[str] = None
    prazos: list[CronogramaPrazoResponse] = Field(default_factory=list)


class CronogramaOrientandoResponse(BaseModel):
    aluno_id: str
    aluno_nome: str
    matricula: Optional[str] = None
    titulo_tcc: str
    tipo_tcc: TipoTCC
    status_tcc: StatusTCC
    prazo_excedido: bool
    alerta_prazo: Optional[str] = None
    papel_orientacao: str
    prazos: list[CronogramaPrazoResponse] = Field(default_factory=list)


class CronogramaPeriodoResponse(BaseModel):
    periodo: PeriodoResumoResponse
    perfil: Perfil
    aluno: Optional[CronogramaAlunoResponse] = None
    orientandos: list[CronogramaOrientandoResponse] = Field(default_factory=list)
    filtro_orientando_id: Optional[str] = None
