from dataclasses import dataclass
from datetime import date


@dataclass
class Periodo:
    id: int
    nome: str
    status: str = "ATIVO"
    data_inicio: date | None = None
    data_fim: date | None = None