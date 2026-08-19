"""Channel-neutral WhatsApp adapter for Bitey.

This adapter normalizes provider webhook payloads into the same ChatRequest
shape used by the web widget. Provider-specific verification/sending remains
outside the core so Bitey behaves identically on WhatsApp and webchat.
"""
from typing import Any

from app.schemas.chat_schema import ChatRequest


def normalize_inbound(payload: dict[str, Any], *, company_id: int = 1) -> ChatRequest:
    """Normalize common WhatsApp webhook fields without coupling to a vendor."""
    message = payload.get("message") or payload.get("text") or payload.get("body") or ""
    phone = payload.get("phone") or payload.get("from") or payload.get("sender") or ""
    conversation_id = payload.get("conversation_id") or payload.get("conversationId") or payload.get("id")
    name = payload.get("name") or payload.get("customer_name")
    language = payload.get("language_preference") or payload.get("language") or "auto"

    return ChatRequest(
        message=str(message).strip(),
        phone=str(phone).strip() or None,
        company_id=company_id,
        customer_name=str(name).strip() if name else None,
        channel="whatsapp",
        conversation_id=str(conversation_id) if conversation_id else None,
        language_preference=str(language),
    )


def build_outbound(response: dict[str, Any]) -> dict[str, Any]:
    """Return a provider-neutral outbound message for a WhatsApp adapter."""
    return {
        "text": response.get("response") or response.get("message") or "",
        "conversation_id": response.get("conversation_id"),
        "customer_id": response.get("customer_id"),
        "language": response.get("language"),
        "intent": response.get("intent"),
        "ticket_id": response.get("ticket_id"),
        "preferred_contact_channel": response.get("preferred_contact_channel"),
    }
