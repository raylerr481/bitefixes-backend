
from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):

    id: int
    empresa_id: int
    cliente_id: int
    conversacion_id: Optional[int] = None

    mensaje: str
    remitente: str
    rol: Optional[str] = None

    intencion: Optional[str] = None
    servicio_id: Optional[int] = None
    ticket_id: Optional[int] = None