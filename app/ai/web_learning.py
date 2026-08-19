"""Governed persistence for verified web evidence."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional

from app.database.supabase import database


def record_web_candidate(*, company_id: int, message: str, web: Dict[str, Any], conversation_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Store verified web evidence as a review candidate; never auto-promote it."""
    verification = web.get("verification") or {}
    if not web.get("learning_candidate") or not verification.get("verified"):
        return None
    sources = web.get("results") or []
    top = sources[0] if sources else {}
    score = float(verification.get("verification_score", 0) or 0)
    try:
        candidate = database.table("semantic_candidates").insert({
            "candidate_type": "web_grounding",
            "proposed_code": None,
            "proposed_name": top.get("title") or "Verified web evidence",
            "description": top.get("snippet"),
            "scope": "company",
            "company_id": company_id,
            "confidence": score,
            "status": "pending",
            "metadata": {
                "conversation_id": conversation_id,
                "queries": web.get("queries", []),
                "verification": verification,
                "sources": sources[:5],
            },
        }).execute()
        row = (candidate.data or [None])[0]
        database.table("semantic_learning_events").insert({
            "event_type": "web_grounding",
            "source_type": "web",
            "source_ref": str(row.get("id")) if row else None,
            "company_id": company_id,
            "scope": "company",
            "input_hash": hashlib.sha256((message or "").strip().lower().encode()).hexdigest(),
            "changes": {"candidate_id": row.get("id") if row else None, "verification": verification},
            "confidence": score,
            "outcome": "candidate_pending_review",
        }).execute()
        return row
    except Exception as exc:
        print("[WEB LEARNING WARNING]", type(exc).__name__)
        return None
