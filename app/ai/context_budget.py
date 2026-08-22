"""Provider-aware context selection, compression, and coverage validation.

This module only prepares transport payloads. It never evaluates or rewrites an
external AI's cognitive answer.
"""
from __future__ import annotations

import os
from typing import Any

from .context_selector import ESSENTIAL_KEYS, compact_value, essential_coverage, select_context

DEFAULT_CHAR_BUDGET = 9000
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
    return str(value).strip()


def _serialized_size(payload: dict[str, Any]) -> int:
    return sum(len(str(k)) + len(_text(v)) + 8 for k, v in payload.items())


def build_context(provider_name: str, context: dict[str, Any] | None) -> dict[str, Any]:
    """Build a bounded package without silently dropping essential categories."""
    source = dict(context or {})
    budget = PROVIDER_CHAR_BUDGETS.get(provider_name, DEFAULT_CHAR_BUDGET)
    selected, selection_meta = select_context(source)

    # Essential categories get a reserved share so a large conversation cannot
    # displace the company's identity, services, capabilities, or current need.
    present_essential = [k for k in ESSENTIAL_KEYS if _text(source.get(k))]
    reserved = max(1, budget // 2) if present_essential else 0
    per_essential = max(256, reserved // max(1, len(present_essential)))

    result: dict[str, Any] = {}
    for key in ESSENTIAL_KEYS:
        if key not in selected:
            continue
        result[key] = compact_value(selected[key], per_essential)

    remaining = max(0, budget - _serialized_size(result))

    # Add relevant dynamic context first, then other selected context.
    dynamic_keys = [k for k in selected if k not in ESSENTIAL_KEYS]
    dynamic_keys.sort(key=lambda k: selection_meta["scores"].get(k, 0), reverse=True)
    for key in dynamic_keys:
        if remaining < 80:
            break
        allowance = max(80, remaining - len(key) - 8)
        value = compact_value(selected[key], allowance)
        if not value:
            continue
        result[key] = value
        remaining -= len(key) + len(value) + 8

    coverage = essential_coverage(result, source)
    # Coverage is a guardrail: if a category was present but got emptied by an
    # extreme budget, restore its smallest useful representation.
    if not coverage["ok"]:
        for key in coverage["missing"]:
            if remaining < 1:
                break
            value = _text(source.get(key))[: max(1, remaining - len(key) - 8)]
            if value:
                result[key] = value
                remaining = max(0, remaining - len(key) - len(value) - 8)
        coverage = essential_coverage(result, source)

    result["_transport"] = {
        "provider": provider_name,
        "char_budget": budget,
        "selected": list(result.keys()),
        "compacted": _serialized_size(source) > _serialized_size(result),
        "coverage_ok": coverage["ok"],
        "coverage_missing": coverage["missing"],
        "selection_relevance": selection_meta["scores"],
    }
    return result
