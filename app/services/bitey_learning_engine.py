"""Bitey incremental cognitive learning layer.

External AIs remain reasoning leaders. Bitey observes, evaluates and stores
business-scoped learning candidates; it does not silently promote guesses to
company truth.
"""
from __future__ import annotations

from typing import Any

from app.database.supabase import supabase_manager


KNOWLEDGE_TYPES = {"linguistic", "concept", "method", "relationship", "policy"}


def _client():
    return getattr(supabase_manager, "client", None)


def build_learning_context(*, company_id: int, message: str, page_context: dict | None = None,
                           service_context: dict | None = None, memory: dict | None = None) -> dict[str, Any]:
    """Build a compact, company-scoped context packet for external AIs."""
    return {
        "company_id": company_id,
        "company_authority": True,
        "page_context": page_context or {},
        "service_context": service_context or {},
        "conversation_memory": memory or {},
        "learning_role": "observe_evaluate_learn",
        "external_ai_role": "reasoning_leader",
        "ticket_policy": "intent_alone_never_creates_ticket",
        "message": message,
    }


def evaluate_external_result(*, response: str, context: dict[str, Any], service: str | None = None) -> dict[str, Any]:
    """Return transparent heuristic evaluation metadata; never claim model training."""
    text = (response or "").strip()
    score = 0.0
    if text:
        score += 0.30
    if context.get("company_authority") and service and service.lower() in text.lower():
        score += 0.30
    if context.get("page_context"):
        score += 0.20
    if context.get("service_context"):
        score += 0.20
    return {
        "score": round(min(score, 1.0), 4),
        "evaluated": True,
        "criteria": ["non_empty", "company_context", "service_alignment", "page_alignment"],
    }


def record_learning_candidate(*, company_id: int, kind: str, title: str, payload: dict[str, Any],
                              confidence: float = 0.0, source: str = "external_ai") -> dict[str, Any]:
    """Persist a candidate only when the learning table exists; failures are non-blocking."""
    if kind not in KNOWLEDGE_TYPES:
        raise ValueError(f"Unsupported learning kind: {kind}")
    client = _client()
    if client is None:
        return {"stored": False, "reason": "supabase_client_unavailable"}
    try:
        result = client.table("bitey_learning_candidates").insert({
            "company_id": company_id,
            "kind": kind,
            "title": title,
            "payload": payload,
            "confidence": max(0.0, min(float(confidence), 1.0)),
            "source": source,
            "status": "candidate",
        }).execute()
        row = (result.data or [None])[0]
        return {"stored": bool(row), "candidate": row}
    except Exception as error:
        return {"stored": False, "reason": str(error)}
