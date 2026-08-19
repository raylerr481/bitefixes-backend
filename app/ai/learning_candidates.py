"""Governed persistence for AI consultation learning candidates."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional

from app.database.supabase import database


def record_candidate(*, company_id: int, message: str, provider: str,
                     suggestion: Dict[str, Any], evaluation: Dict[str, Any],
                     conversation_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Store an AI suggestion for review; never promote it automatically."""
    try:
        confidence = float(evaluation.get("score", 0) or 0)
        candidate = database.table("semantic_candidates").insert({
            "candidate_type": "ai_consultation",
            "proposed_code": suggestion.get("intent"),
            "proposed_name": suggestion.get("need") or suggestion.get("intent"),
            "description": suggestion.get("answer") or suggestion.get("text"),
            "scope": "company",
            "company_id": company_id,
            "confidence": confidence,
            "status": "pending",
            "metadata": {"provider": provider, "conversation_id": conversation_id,
                         "evaluation": evaluation},
        }).execute()
        row = (candidate.data or [None])[0]
        database.table("semantic_learning_events").insert({
            "event_type": "ai_consultation",
            "source_type": provider,
            "source_ref": str(row.get("id")) if row else None,
            "company_id": company_id,
            "scope": "company",
            "input_hash": hashlib.sha256((message or "").strip().lower().encode()).hexdigest(),
            "changes": {"candidate_id": row.get("id") if row else None, "evaluation": evaluation},
            "confidence": confidence,
            "outcome": "candidate_pending_review",
        }).execute()
        return row
    except Exception as exc:
        print("[AI LEARNING WARNING]", exc)
        return None
