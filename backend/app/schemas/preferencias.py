from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class PreferenciasNotificacao(BaseModel):
    email_prazos_orientandos: bool = True
    antecedencia_dias: int = Field(default=3, ge=1, le=30)
    email_notas_parciais: bool = True
    email_notas_finais: bool = True


class ConsentimentoLgpd(BaseModel):
    publicar_portal_publico: bool = False
    compartilhar_terceiros: bool = False
    atualizado_em: datetime | None = None

    @field_validator("atualizado_em", mode="before")
    @classmethod
    def ignore_client_timestamp(cls, value):
        return value
