"""Per-provider context budgeting for Bitey's external AI transport layer.

This module only compacts transport payloads. It does not judge, score, or
rewrite an external model's cognitive answer.
"""
from __future__ import annotations

import json
import os
from typing import Any

DEFAULT_CHAR_BUDGET = 9000

# Conservative payload budgets. They are transport limits, not quality scores.
PROVIDER_CHAR_BUDGETS = {
    "groq": int(os.getenv("GROQ_CONTEXT_CHAR_BUDGET", "7000")),
    "qwen-free": int(os.getenv("QWEN_CONTEXT_CHAR_BUDGET", "9000")),
    "deepseek-free": int(os.getenv("DEEPSEEK_CONTEXT_CHAR_BUDGET", "9000")),
    "huggingface": int(os.getenv("HF_CONTEXT_CHAR_BUDGET", "9000")),
    "cloudflare-free": int(os.getenv("CLOUDFLARE_CONTEXT_CHAR_BUDGET", "9000")),
}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return str(value)


def _clip(text: str, limit: int) -> str:
    text = _text(text)
    if len(text) <= limit:
        return text
    if limit < 120:
        return text[:limit]
    head = int(limit * 0.72)
    tail = limit - head - 32
    return text[:head] + "\n...[context compacted]...\n" + text[-max(0, tail):]


def build_context(provider_name: str, context: dict[str, Any] | None) -> dict[str, Any]:
    """Keep high-value company/current-query context while bounding transport size."""
    source = context or {}
    budget = PROVIDER_CHAR_BUDGETS.get(provider_name, DEFAULT_CHAR_BUDGET)

    # Preserve these fields first; they define the company and the user's need.
    priority = (
        "company_context",
        "company",
        "services",
        "capabilities",
        "user_query",
        "current_message",
        "conversation",
        "memory",
        "sources",
        "tools",
    )
    result: dict[str, Any] = {}
    remaining = budget

    for key in priority:
        if key not in source or remaining <= 0:
            continue
        value = _text(source[key])
        if not value:
            continue
        # Reserve a little framing space for the key and JSON syntax.
        allowance = max(0, remaining - len(key) - 12)
        compacted = _clip(value, allowance)
        result[key] = compacted
        remaining -= len(compacted) + len(key) + 8

    # Include other context only when room remains; never let it displace the
    # company identity or current user need above.
    if remaining > 200:
        for key, value in source.items():
            if key in result or key in priority:
                continue
            compacted = _clip(value, max(0, remaining - len(key) - 8))
            if not compacted:
                continue
            result[key] = compacted
            remaining -= len(compacted) + len(key) + 8
            if remaining <= 200:
                break

    result["_transport"] = {
        "provider": provider_name,
        "char_budget": budget,
        "compacted": len(_text(source)) > len(_text(result)),
    }
    return result
