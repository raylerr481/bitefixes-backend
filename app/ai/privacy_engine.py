"""Protected context boundary for external AI consultation.

External providers receive the minimum useful technical context. Private
identity and operational fields are never forwarded by default.
"""
from __future__ import annotations

import re
from typing import Any, Dict

SENSITIVE_KEYS = {
    "password", "passwd", "secret", "token", "api_key", "apikey", "authorization",
    "cpf", "cnpj", "ssn", "credit_card", "card_number", "bank_account", "address",
    "email", "phone", "telephone", "whatsapp", "full_name", "name", "customer_id",
    "ticket_id", "ticket", "internal_notes", "private_notes", "credentials",
}

SENSITIVE_PATTERNS = [
    re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),  # CPF
    re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"),  # CNPJ
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    re.compile(r"\b(?:\+?\d[\d ()-]{7,}\d)\b"),
]


def _redact_text(value: str) -> str:
    result = str(value)
    for pattern in SENSITIVE_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


def sanitize(value: Any, *, depth: int = 0) -> Any:
    """Recursively remove sensitive fields and redact sensitive free text."""
    if depth > 5:
        return "[TRUNCATED]"
    if isinstance(value, dict):
        safe: Dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).lower().strip()
            if normalized in SENSITIVE_KEYS or any(part in normalized for part in ("password", "secret", "token", "credential", "api_key")):
                continue
            safe[str(key)] = sanitize(item, depth=depth + 1)
        return safe
    if isinstance(value, (list, tuple)):
        return [sanitize(item, depth=depth + 1) for item in value[:20]]
    if isinstance(value, str):
        return _redact_text(value)[:4000]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return _redact_text(str(value))[:1000]


def build_external_context(*, intent: Dict[str, Any], business_context: Dict[str, Any] | None = None,
                           knowledge: Any = None, memory: Any = None) -> Dict[str, Any]:
    """Build an external-safe context without exposing customer identity."""
    return sanitize({
        "intent": {"intent": intent.get("intent"), "confidence": intent.get("confidence", 0)},
        "business_context": business_context or {},
        "knowledge": knowledge,
        "memory": memory,
    })
