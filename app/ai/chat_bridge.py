"""Safe bridge between Bitey Core and external AI providers."""
import json
import re
from typing import Any

from app.services.ai_provider import ai_provider
from .policy import sanitize_context


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def enrich_intent(
    message: str,
    *,
    language: str | None = None,
    current_intent: str | None = None,
    current_confidence: float = 0,
) -> dict[str, Any]:
    """Ask an external model for an advisory interpretation only when needed."""
    if current_intent and float(current_confidence or 0) >= 0.80:
        return {"used": False, "reason": "core_confident"}
    if not ai_provider.available():
        return {"used": False, "reason": "no_provider"}

    system = """You are a semantic assistant inside Bitey. You are advisory only.
Return ONLY valid JSON with keys: intent, need, entities, confidence, language.
Use one of these canonical intents when applicable: mobile_repair, computer_repair,
hardware_upgrade, network_configuration, cctv_installation, remote_support,
ai_assistant, sales, quote, purchase, software_problem, general_information.
Do not create tickets, prices, customers, workflows or actions. Never invent business facts.
Map spelling mistakes, slang and multilingual expressions to canonical concepts.
"""
    context = sanitize_context({
        "language": language,
        "current_intent": current_intent,
        "current_confidence": current_confidence,
    })
    prompt = f"User message: {message}"
    text = ai_provider.respond(system, prompt, context=context)
    parsed = _extract_json(text or "")
    if not parsed:
        return {"used": True, "valid": False, "raw": text}

    try:
        confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0))))
    except (TypeError, ValueError):
        confidence = 0.0
    parsed["confidence"] = confidence
    parsed["used"] = True
    parsed["provider"] = "openrouter_or_openai"
    return parsed
