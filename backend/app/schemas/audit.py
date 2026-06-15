from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    usuario_nome: str
    usuario_email: str
    usuario_perfil: str
    acao: str
    entidade: str | None = None
    descricao: str
    criado_em: datetime
