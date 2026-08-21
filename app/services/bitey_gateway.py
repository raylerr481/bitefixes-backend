"""Bitey Cloud Gateway - public facade for every channel.

Bitey is the product identity and transport facade at this stage. It is not
claimed to be the primary cognitive model yet. Conversation reasoning may be
performed directly by configured external AI providers (Groq/open-source
providers through the governed AI council), while Bitey infrastructure stores
context, memory, telemetry and protected business state underneath.

This separation is intentional: external AI answers the user today; Bitey
provides the channel, context and business infrastructure that will allow Bitey
Core to acquire and validate its own capabilities later.
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
    """Return a stable public contract while keeping AI orchestration internal."""
    if os.getenv("BITEY_PUBLIC_DEBUG", "false").lower() == "true":
        return result

    public = {k: v for k, v in result.items() if k not in _INTERNAL_KEYS}
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
    """Expose Bitey as the single public facade for every channel.

    ``process_message`` runs the Bitey infrastructure and governed external-AI
    consultation. For ordinary conversation turns, the configured external AI
    provider is currently the cognitive responder; protected tickets, quotes
    and business workflows remain under Bitey's deterministic controls.
    """
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
        return {
            "success": False,
            "response": "No fue posible procesar la solicitud.",
            "public_contract": "bitey-chat-v1",
        }

    public = _public_result(result)
    public["gateway"] = {
        "channel": normalized_channel,
        "architecture": "bitey-public-facade",
        "cognitive_responder": "external-ai",
        "business_infrastructure": "bitey",
    }
    if preferred_contact_channel:
        public["preferred_contact_channel"] = preferred_contact_channel
    return public
