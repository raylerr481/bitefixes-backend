from pydantic import BaseModel
from typing import Optional


class Company(BaseModel):
    id: int
    name: str
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    plan: Optional[str] = "free"
    business_type: Optional[str] = None
    slug: Optional[str] = None
    is_active: bool = True