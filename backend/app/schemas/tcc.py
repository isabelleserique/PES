from pydantic import BaseModel, Field
from typing import Optional
from backend.app.models.tcc import TipoTCC


class TCCCreateRequest(BaseModel):
    titulo: str = Field(min_length=3)
    tipo: TipoTCC
    orientador_id: str
    coorientador_id: Optional[str] = None


class TCCResponse(BaseModel):
    id: str
    titulo: str
    tipo: TipoTCC
    status: str
    prazo_excedido: bool