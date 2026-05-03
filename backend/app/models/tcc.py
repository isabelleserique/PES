from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class TipoTCC(str, Enum):
    MONOGRAFIA = "MONOGRAFIA"
    ARTIGO = "ARTIGO"
    RELATORIO = "RELATORIO"

class StatusTCC(str, Enum):
    RASCUNHO = "RASCUNHO"
    AGUARDANDO_ACEITE = "AGUARDANDO_ACEITE"
    APROVADO = "APROVADO"
    REJEITADO = "REJEITADO"

@dataclass
class TCC:
    id: str
    titulo: str
    tipo: TipoTCC
    aluno_id: str
    orientador_id: str
    coorientador_id: Optional[str]
    periodo: str
    status: StatusTCC
    prazo_excedido: bool
    criado_em: datetime
