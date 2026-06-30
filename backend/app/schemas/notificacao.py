from __future__ import annotations

from pydantic import BaseModel


class NotificacaoPrazoResultado(BaseModel):
    avaliadas: int = 0
    enviadas: int = 0
    ignoradas: int = 0
