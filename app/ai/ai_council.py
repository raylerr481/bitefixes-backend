"""Bounded multi-provider consultation. Bitey remains the final evaluator."""
from typing import Any, Dict, List

from app.services.ai_provider import ai_provider


def consult(message: str, *, language: str, context: Dict[str, Any], max_providers: int = 2) -> List[Dict[str, Any]]:
    if not ai_provider.available():
        return []
    results = []
    # Provider routing is deliberately centralized in AIProvider. A single call
    # can use the configured free route first, with paid fallback only if enabled.
    text = ai_provider.respond(
        "You are a bounded Bitey consultant. Analyze the request and return a concise "
        "structured recommendation. Do not execute actions or invent business facts.",
        message,
        context={**context, "language": language},
    )
    if text:
        results.append({"provider": ai_provider.name(), "answer": text})
    return results[:max_providers]
