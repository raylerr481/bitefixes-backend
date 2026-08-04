from pydantic import BaseModel
from typing import Optional


class Customer(BaseModel):
    id: int
    empresa_id: int
    nombre: str
    telefono: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None