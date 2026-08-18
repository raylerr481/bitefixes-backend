"""Bitey Chat Schemas V18."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    phone: str = "web"
    company_id: int = 1
    customer_name: str = "Customer"
    channel: str = "website"
    conversation_id: str | None = None
    language_preference: str = "auto"


class ChatResponse(BaseModel):
    success: bool = True
    response: str
    intent: str | None = None
    ticket_id: int | None = None
    conversation_id: str | None = None
    language: str | None = None
    language_source: str | None = None
