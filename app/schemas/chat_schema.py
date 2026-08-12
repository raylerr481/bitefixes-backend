"""
Bitey Chat Schema V17
"""

from pydantic import BaseModel



class ChatRequest(BaseModel):

    message: str

    phone: str

    company_id: int = 1

    customer_name: str = "Customer"

    channel: str = "website"



class ChatResponse(BaseModel):

    success: bool = True

    response: str

    intent: str | None = None

    ticket_id: int | None = None