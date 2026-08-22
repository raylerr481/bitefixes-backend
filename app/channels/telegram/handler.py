"""Telegram channel adapter for Bitey API.

Provider transport (Bot API send) is deliberately kept outside the cognitive core.
"""
from __future__ import annotations
from typing import Any
from app.channels.base import InboundEvent
from app.schemas.chat_schema import ChatRequest


def normalize_inbound(payload: dict[str, Any], *, company_id: int = 1) -> InboundEvent | None:
    msg = payload.get("message") or payload.get("edited_message") or payload.get("channel_post") or {}
    text = str(msg.get("text") or "").strip()
    if not text:
        return None
    sender = msg.get("from") or {}
    chat = msg.get("chat") or {}
    conversation_id = str(chat.get("id") or sender.get("id") or msg.get("message_id") or "")
    request = ChatRequest(
        message=text, company_id=company_id, channel="telegram",
        customer_name=str(sender.get("first_name") or "").strip() or None,
        last_name=str(sender.get("last_name") or "").strip() or None,
        conversation_id=conversation_id or None,
        language_preference="auto",
    )
    return InboundEvent(request=request, provider_message_id=str(msg.get("message_id") or "") or None)


def build_outbound(response: dict[str, Any]) -> dict[str, Any]:
    return {"text": response.get("response") or response.get("message") or "", "conversation_id": response.get("conversation_id")}
