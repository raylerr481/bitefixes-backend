"""Semantic-first routing helpers for Bitey."""
from typing import Any

from .policy import task_allowed


async def route_message(
    message: str,
    *,
    semantic_result: dict[str, Any] | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    """Build an AI task without granting business-action authority."""
    semantic_result = semantic_result or {}
    intent = semantic_result.get("intent")
    need = semantic_result.get("need")

    # Clear deterministic cases stay inside Bitey Core.
    if intent in {"greeting", "general_information"}:
        return {"mode": "core", "task": "general_reasoning", "intent": intent}

    task = "semantic_interpretation" if not intent else "response_generation"
    if intent in {"computer_repair", "mobile_repair", "network_configuration", "cctv_installation"}:
        task = "technical_diagnosis"

    if not task_allowed(task):
        task = "semantic_interpretation"

    return {
        "mode": "ai",
        "task": task,
        "intent": intent,
        "need": need,
        "language": language,
        "message": message,
    }
