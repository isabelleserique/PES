from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Perfil(str, Enum):
    COORDENADOR = "COORDENADOR"
    ALUNO = "ALUNO"
    ORIENTADOR = "ORIENTADOR"


class StatusCadastro(str, Enum):
    PENDENTE = "PENDENTE"
    ATIVO = "ATIVO"
    REJEITADO = "REJEITADO"


@dataclass
class User:
    id: str
    nome_completo: str
    email: str
    username: str
    senha_hash: str
    perfil: Perfil
    matricula: Optional[str]
    status: StatusCadastro
    failed_login_attempts: int
    blocked_until: Optional[datetime]
    ativo: bool
    criado_em: datetime
