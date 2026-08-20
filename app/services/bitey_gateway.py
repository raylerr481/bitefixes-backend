"""Bitey Cloud Gateway - one normalized entry point for every channel.

Channels are transport adapters. Business intelligence stays in Bitey Core.
"""
from __future__ import annotations

from typing import Any

from app.core.bitey import process_message


SUPPORTED_CHANNELS = {
    "website", "whatsapp", "messenger", "telegram", "email", "sms",
    "phone", "app", "private", "api",
}


def normalize_channel(channel: str | None) -> str:
    value = str(channel or "website").strip().lower()
    return value if value in SUPPORTED_CHANNELS else "api"


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
    result = process_message(
        company_id=company_id,
        message=message,
        phone=phone,
        email=email,
        customer_name=customer_name,
        last_name=last_name,
        channel=normalize_channel(channel),
        conversation_id=conversation_id,
        language_preference=language_preference,
    )
    if isinstance(result, dict):
        result["gateway"] = {
            "channel": normalize_channel(channel),
            "architecture": "bitey-cloud-gateway",
            "brain": "bitey-core",
        }
        if preferred_contact_channel:
            result["preferred_contact_channel"] = preferred_contact_channel
    return result
