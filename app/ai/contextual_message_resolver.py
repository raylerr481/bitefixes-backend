"""Bounded conversation resolver used by the existing Bitey gateway.

This module only resolves continuity and identifies public-research candidates.
It does not search the web, select an external model, invent facts, or judge
responses. The existing web_intelligence and external-AI layers remain in charge.
"""
from __future__ import annotations

import re
from typing import Any


def _looks_like_public_entity(message: str) -> bool:
    text = " ".join(str(message or "").split())
    if not text or len(text.split()) < 2:
        return False
    return bool(re.search(r"\b(?:[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.-]{2,})(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ.-]{2,})+\b", text))


def _history_url(history: list[dict[str, Any]]) -> str | None:
    for row in reversed(history[-8:]):
        content = str(row.get("content") or row.get("message_content") or "") if isinstance(row, dict) else ""
        match = re.search(r"https?://[^\s)>]+", content)
        if match:
            return match.group(0).rstrip(".,;]")
    return None


def resolve_contextual_message(
    message: str,
    *,
    history: list[dict[str, Any]] | None = None,
    active_entity: str | None = None,
    active_goal: str | None = None,
) -> dict[str, Any]:
    """Resolve short follow-ups and flag named public entities for research."""
    raw = " ".join(str(message or "").strip().split())
    turns = history or []
    subject = str(active_entity or "").strip()
    goal = str(active_goal or "").strip()
    recent_text = " ".join(str(row.get("content") or row.get("message_content") or "") for row in turns[-6:] if isinstance(row, dict))
    active_url = _history_url(turns)
    short = len(raw.split()) <= 8

    if short and subject:
        resolved = f"{subject}: {raw}"
        if active_url:
            resolved += f" [context_url: {active_url}]"
        if goal:
            resolved += f" (objetivo: {goal})"
        return {"resolved_message": resolved, "needs_clarification": False, "research_candidate": False, "active_entity": subject, "active_goal": goal or None, "active_url": active_url}

    if _looks_like_public_entity(raw):
        return {"resolved_message": raw, "needs_clarification": False, "research_candidate": True, "active_entity": raw, "active_goal": goal or None, "active_url": active_url}

    if short and recent_text:
        return {"resolved_message": f"{recent_text[-500:]} | Seguimiento: {raw}", "needs_clarification": False, "research_candidate": False, "active_entity": subject or None, "active_goal": goal or None, "active_url": active_url}

    return {"resolved_message": raw, "needs_clarification": False, "research_candidate": False, "active_entity": subject or None, "active_goal": goal or None, "active_url": active_url}
