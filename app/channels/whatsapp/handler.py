"""WhatsApp channel adapter for Bitey API."""
from __future__ import annotations
from typing import Any
from app.channels.base import InboundEvent
from app.schemas.chat_schema import ChatRequest


def normalize_inbound(payload: dict[str, Any], *, company_id: int = 1) -> InboundEvent | None:
    # Accept both canonical test payloads and common WhatsApp webhook fields.
    entry = (payload.get("entry") or [{}])[0]
    change = ((entry.get("changes") or [{}])[0]).get("value") or {}
    messages = change.get("messages") or []
    if messages:
        msg = messages[0]
        text = str((msg.get("text") or {}).get("body") or "").strip()
        contact = (change.get("contacts") or [{}])[0]
        profile = contact.get("profile") or {}
        phone = str(msg.get("from") or contact.get("wa_id") or "").strip()
        conversation_id = phone or str(msg.get("id") or "")
        name = str(profile.get("name") or "").strip() or None
        provider_id = str(msg.get("id") or "").strip() or None
    else:
        text = str(payload.get("message") or payload.get("text") or payload.get("body") or "").strip()
        phone = str(payload.get("phone") or payload.get("from") or payload.get("sender") or "").strip()
        conversation_id = str(payload.get("conversation_id") or payload.get("conversationId") or payload.get("id") or phone)
        name = str(payload.get("name") or payload.get("customer_name") or "").strip() or None
        provider_id = str(payload.get("message_id") or "").strip() or None
    if not text:
        return None
    request = ChatRequest(
        message=text, phone=phone or None, company_id=company_id,
        customer_name=name, channel="whatsapp", conversation_id=conversation_id or None,
        language_preference=str(payload.get("language_preference") or payload.get("language") or "auto"),
    )
    return InboundEvent(request=request, provider_message_id=provider_id)


def build_outbound(response: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": response.get("response") or response.get("message") or "",
        "conversation_id": response.get("conversation_id"),
        "customer_id": response.get("customer_id"),
        "language": response.get("language"),
        "intent": response.get("intent"),
        "ticket_id": response.get("ticket_id"),
        "preferred_contact_channel": response.get("preferred_contact_channel"),
    }
