"""Persistence for governed answer-comparison telemetry."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional

from app.database.supabase import database


def record_comparison(
    *,
    company_id: int,
    conversation_id: Any,
    message: str,
    intent: Optional[str],
    core_confidence: float,
    consultation_used: bool,
    comparison: Dict[str, Any],
) -> None:
    try:
        selected = comparison.get("selected") or {}
        database.table("ai_answer_comparisons").insert({
            "company_id": company_id,
            "conversation_id": str(conversation_id) if conversation_id is not None else None,
            "message_hash": hashlib.sha256((message or "").strip().lower().encode()).hexdigest(),
            "intent": intent,
            "core_confidence": float(core_confidence or 0),
            "consultation_used": bool(consultation_used),
            "selected_source": selected.get("source"),
            "selected_provider": selected.get("provider"),
            "selected_score": selected.get("score"),
            "reason": comparison.get("reason"),
            "candidates": comparison.get("ranked", []),
        }).execute()
    except Exception as exc:
        print("[AI COMPARISON AUDIT WARNING]", type(exc).__name__)
