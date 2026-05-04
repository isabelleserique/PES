from dataclasses import dataclass
from datetime import date

@dataclass
class Prazo:
    nome: str
    data_limite: date
    tipo_tcc: str 