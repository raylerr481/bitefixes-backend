"""Canonical contracts for Bitey Core 2.0.

The plugin, API, Core, AI providers and persistence layer communicate through
these stable concepts. External AI never receives authority to mutate business
state directly.
"""
from typing import Any, Dict, Optional

SUPPORTED_LANGUAGES = {"es", "pt-BR", "en"}
LANGUAGE_MODES = {"auto", *SUPPORTED_LANGUAGES}


def normalize_language(value: Optional[str]) -> str:
    value = str(value or "auto").strip().lower().replace("_", "-")
    if value in {"pt", "pt-br"}:
        return "pt-BR"
    if value in {"es", "en", "auto"}:
        return value
    return "auto"


def build_chat_context(
    *, company_id: int, message: str, phone: str = "", customer_name: str = "Customer",
    channel: str = "website", conversation_id: Optional[str] = None,
    language_preference: str = "auto"
) -> Dict[str, Any]:
    return {
        "company_id": int(company_id),
        "message": str(message or "").strip(),
        "phone": str(phone or "").strip(),
        "customer_name": str(customer_name or "Customer").strip() or "Customer",
        "channel": str(channel or "website").strip() or "website",
        "conversation_id": str(conversation_id).strip() if conversation_id else None,
        "language_preference": normalize_language(language_preference),
    }
