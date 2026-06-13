from enum import Enum

class StatusPrazo(str, Enum):
    A_VENCER = "A_VENCER"
    PROXIMO = "PROXIMO"
    HOJE = "HOJE"
    VENCIDO = "VENCIDO"

class CorPrazo(str, Enum):
    VERDE = "verde"
    AMARELO = "amarelo"
    LARANJA = "laranja"
    VERMELHO = "vermelho"