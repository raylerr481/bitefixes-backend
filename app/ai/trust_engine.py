"""Adaptive reputation for advisory AI providers.

Trust is evidence-based and capability-specific. It never grants business
authority to an external provider.
"""
from __future__ import annotations

from typing import Any, Dict

from app.database.supabase import database


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def score_provider(provider: str, capability: str = "general_reasoning") -> float:
    """Read historical trust when available; fail closed to a neutral prior."""
    try:
        rows = database.table("ai_provider_trust").select("trust_score").eq("provider", provider).eq("capability", capability).limit(1).execute().data or []
        if rows:
            return _clamp(rows[0].get("trust_score", 0.5))
    except Exception:
        pass
    return 0.5


def rank_candidates(candidates: list[dict[str, Any]], capability: str = "general_reasoning") -> list[dict[str, Any]]:
    ranked = []
    for candidate in candidates:
        item = dict(candidate)
        item["trust_score"] = round(score_provider(item.get("provider", "unknown"), capability), 3)
        ranked.append(item)
    return sorted(ranked, key=lambda item: item["trust_score"], reverse=True)


def record_outcome(provider: str, capability: str, *, correct: bool, weight: float = 0.08) -> Dict[str, Any]:
    """Apply a small bounded reputation update; database is optional."""
    current = score_provider(provider, capability)
    target = 1.0 if correct else 0.0
    updated = round(_clamp(current + (target - current) * _clamp(weight)), 4)
    try:
        database.table("ai_provider_trust").upsert({
            "provider": provider,
            "capability": capability,
            "trust_score": updated,
        }, on_conflict="provider,capability").execute()
    except Exception:
        pass
    return {"provider": provider, "capability": capability, "previous": current, "updated": updated}
