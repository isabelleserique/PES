from __future__ import annotations

from enum import Enum


class StatusTCC(str, Enum):
    AGUARDANDO_ACEITE = "AGUARDANDO_ACEITE"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    APROVADO = "APROVADO"
    REJEITADO = "REJEITADO"


class AcaoEdicaoTCC(str, Enum):
    CRIACAO = "CRIACAO"
    EDICAO = "EDICAO"
