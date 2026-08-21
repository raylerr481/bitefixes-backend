"""Safe, trust-aware evaluation helpers for multi-model answers."""
from __future__ import annotations

import re
from typing import Any


def _normalize_answer(answer: str) -> str:
    return re.sub(r"\s+", " ", str(answer).strip().lower())


def evaluate_candidates(candidates: list[dict[str, Any]], *, core_confidence: float = 0.0) -> dict[str, Any]:
    """Evaluate advisory answers; external models never gain business authority."""
    valid = [c for c in candidates if c.get("answer")]
    if not valid:
        return {"status": "no_candidates", "confidence": 0.0, "consensus": None, "learning_candidate": False}

    groups: dict[str, dict[str, Any]] = {}
    for candidate in valid:
        key = _normalize_answer(candidate["answer"])
        group = groups.setdefault(key, {"answer": str(candidate["answer"]).strip(), "providers": [], "trust": 0.0})
        trust = float(candidate.get("trust_score", 0.5) or 0.5)
        group["providers"].append(candidate.get("provider", "unknown"))
        group["trust"] += max(0.0, min(1.0, trust))

    ranked = sorted(groups.values(), key=lambda item: (item["trust"], len(item["providers"])), reverse=True)
    winner = ranked[0]
    provider_coverage = min(1.0, len(winner["providers"]) / max(1, len(valid)))
    trust_support = min(1.0, winner["trust"] / max(1, len(winner["providers"])))
    core = min(max(float(core_confidence), 0.0), 1.0)
    score = round((provider_coverage * 0.35) + (trust_support * 0.35) + (core * 0.30), 3)
    consensus = winner["answer"] if provider_coverage >= 0.5 else None

    return {
        "status": "evaluated",
        "confidence": score,
        "consensus": consensus,
        "candidate_count": len(valid),
        "providers": winner["providers"],
        "trust_support": round(trust_support, 3),
        "learning_candidate": bool(consensus and score >= 0.75),
    }
