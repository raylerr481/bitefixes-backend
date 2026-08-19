"""Governed AI orchestration for Bitey.

External models are advisory. Bitey Core remains the authority for tenant
context, semantics, services, workflows, tools, tickets and persistence.
"""
from typing import Any, Dict

from app.services.ai_provider import ai_provider


def enrich(message: str, *, language: str, intent: Dict[str, Any] | None = None) -> Dict[str, Any]:
    intent = intent or {}
    if not ai_provider.available():
        return {"used": False, "reason": "no_provider"}
    system = (
        "You are Bitey's advisory semantic layer. Return JSON only with keys "
        "intent, need, entities, confidence, language. Never create tickets, "
        "change customers, execute tools, invent prices or business facts. "
        "Use canonical intents from the business context."
    )
    context = {
        "language": language,
        "current_intent": intent.get("intent"),
        "current_confidence": intent.get("confidence", 0),
    }
    try:
        text = ai_provider.respond(system, message, context=context)
        return {"used": bool(text), "text": text, "provider": ai_provider.name()}
    except Exception as exc:
        return {"used": False, "reason": type(exc).__name__}
