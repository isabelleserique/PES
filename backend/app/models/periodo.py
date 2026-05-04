from __future__ import annotations

from enum import Enum


class TipoTCC(str, Enum):
    TODOS = "Todos"
    MONOGRAFIA = "Monografia"
    ARTIGO = "Artigo"
    RELATORIO_ESTAGIO = "Relatorio de Estagio"
