"""Bitey Cloud Gateway - one normalized public entry point for every channel.

Channels are transport adapters. Business intelligence stays in Bitey Core.
Internal AI reasoning is never exposed to end users unless explicitly enabled
for controlled debugging.
"""
from __future__ import annotations

import os
from typing import Any

from app.core.bitey import process_message

SUPPORTED_CHANNELS = {
    "website", "whatsapp", "messenger", "telegram", "email", "sms",
    "phone", "app", "private", "api",
}

_INTERNAL_KEYS = {
    "intent", "confidence", "raw_intent_score", "knowledge", "knowledge_found",
    "memory", "ai_consultation", "comparative_evaluation", "response_source",
    "decision", "gateway_debug",
}


def normalize_channel(channel: str | None) -> str:
    value = str(channel or "website").strip().lower()
    return value if value in SUPPORTED_CHANNELS else "api"


def _public_result(result: dict[str, Any]) -> dict[str, Any]:
    """Return a stable public contract and keep orchestration telemetry internal."""
    if os.getenv("BITEY_PUBLIC_DEBUG", "false").lower() == "true":
        return result

    public = {k: v for k, v in result.items() if k not in _INTERNAL_KEYS}
    # Keep a minimal machine-readable status for channel adapters.
    public["public_contract"] = "bitey-chat-v1"
    return public


def handle_message(
    *,
    company_id: int,
    message: str,
    channel: str = "website",
    phone: str = "",
    email: str = "",
    customer_name: str = "Customer",
    last_name: str = "",
    conversation_id: str | None = None,
    language_preference: str = "auto",
    preferred_contact_channel: str | None = None,
) -> dict[str, Any]:
    """Normalize channel context and delegate to the single Bitey brain."""
    normalized_channel = normalize_channel(channel)
    result = process_message(
        company_id=company_id,
        message=message,
        phone=phone,
        email=email,
        customer_name=customer_name,
        last_name=last_name,
        channel=normalized_channel,
        conversation_id=conversation_id,
        language_preference=language_preference,
    )
    if not isinstance(result, dict):
        return {"success": False, "response": "No fue posible procesar la solicitud.", "public_contract": "bitey-chat-v1"}

    # Never leak provider comparisons, confidence scores, internal decisions or
    # knowledge payloads through the production chat surface.
    public = _public_result(result)
    public["gateway"] = {
        "channel": normalized_channel,
        "architecture": "bitey-cloud-gateway",
        "brain": "bitey-core",
    }
    if preferred_contact_channel:
        public["preferred_contact_channel"] = preferred_contact_channel
    return public
