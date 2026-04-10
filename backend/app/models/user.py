from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Perfil(StrEnum):
    COORDENADOR = "COORDENADOR"
    ALUNO = "ALUNO"
    ORIENTADOR = "ORIENTADOR"


@dataclass(slots=True)
class User:
    id: str
    nome_completo: str
    email: str
    username: str
    senha_hash: str
    perfil: Perfil
    ativo: bool
    criado_em: datetime

