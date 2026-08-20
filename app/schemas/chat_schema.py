"""Bitey Chat Schemas - unified cloud gateway contract."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    phone: str | None = None
    email: str | None = None
    company_id: int = 1
    customer_name: str | None = None
    last_name: str | None = None
    channel: str = "website"
    conversation_id: str | None = None
    language_preference: str = "auto"
    preferred_contact_channel: str | None = None


class ChatResponse(BaseModel):
    success: bool = True
    response: str
    intent: str | None = None
    ticket_id: int | None = None
    conversation_id: str | None = None
    language: str | None = None
    language_source: str | None = None
    preferred_contact_channel: str | None = None
