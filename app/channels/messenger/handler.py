"""Meta Messenger channel adapter for Bitey API.

Webhook normalization is isolated from the Bitey cognitive/learning core.
"""
from __future__ import annotations
from typing import Any
from app.channels.base import InboundEvent
from app.schemas.chat_schema import ChatRequest


def normalize_inbound(payload: dict[str, Any], *, company_id: int = 1) -> InboundEvent | None:
    entry = (payload.get("entry") or [{}])[0]
    event = (entry.get("messaging") or [{}])[0]
    message = event.get("message") or {}
    text = str(message.get("text") or "").strip()
    sender = event.get("sender") or {}
    sender_id = str(sender.get("id") or "")
    if not text or not sender_id:
        return None
    request = ChatRequest(
        message=text, company_id=company_id, channel="messenger",
        conversation_id=sender_id, language_preference="auto",
    )
    return InboundEvent(request=request, provider_message_id=str(event.get("message", {}).get("mid") or "") or None)


def build_outbound(response: dict[str, Any]) -> dict[str, Any]:
    return {"text": response.get("response") or response.get("message") or "", "conversation_id": response.get("conversation_id")}
