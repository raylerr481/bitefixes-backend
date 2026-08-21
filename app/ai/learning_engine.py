"""Incremental learning without automatic code mutation.

Only validated, de-identified patterns become learning candidates. The
knowledge store is optional so Bitey keeps working if the learning tables are
not provisioned yet.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict

from app.ai.privacy_engine import sanitize
from app.database.supabase import database


def fingerprint(text: str) -> str:
    return hashlib.sha256(str(text).strip().lower().encode("utf-8")).hexdigest()[:32]


def learn_pattern(*, message: str, intent: str | None, evaluation: Dict[str, Any], source: str = "ai_council") -> Dict[str, Any]:
    """Store only de-identified, sufficiently supported learning candidates."""
    confidence = float(evaluation.get("confidence", 0) or 0)
    if not intent or confidence < 0.75:
        return {"stored": False, "reason": "insufficient_validation"}

    candidate = {
        "pattern_hash": fingerprint(message),
        "intent": intent,
        "source": source,
        "confidence": round(min(confidence, 1.0), 4),
        "pattern": sanitize(str(message))[:500],
        "validated": True,
    }
    try:
        database.table("learning_patterns").upsert(candidate, on_conflict="pattern_hash,intent").execute()
        return {"stored": True, "candidate": candidate}
    except Exception as exc:
        # Learning must never break the customer response path.
        return {"stored": False, "reason": "learning_store_unavailable", "error": type(exc).__name__, "candidate": candidate}
