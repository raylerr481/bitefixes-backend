"""Deterministic evaluation of external AI suggestions."""
from __future__ import annotations

from typing import Any, Dict, List


def evaluate_suggestions(suggestions: List[Dict[str, Any]], *, core_confidence: float = 0.0) -> Dict[str, Any]:
    valid = [item for item in suggestions if str(item.get("answer") or "").strip()]
    if not valid:
        return {
            "status": "no_suggestions",
            "score": 0.0,
            "selected": None,
            "candidate_count": 0,
            "learning_candidate": False,
        }

    base = min(max(float(core_confidence or 0), 0.0), 1.0)
    ranked = []
    for index, item in enumerate(valid):
        answer = str(item.get("answer", "")).strip()
        provider_bonus = 0.05 if item.get("provider") else 0.0
        length_signal = min(1.0, len(answer) / 800.0)
        score = (0.55 * (1.0 - base)) + (0.30 * length_signal) + provider_bonus
        ranked.append({**item, "evaluation_score": round(min(1.0, score), 4), "rank": index + 1})

    ranked.sort(key=lambda x: x["evaluation_score"], reverse=True)
    selected = ranked[0]
    score = round(selected["evaluation_score"], 4)
    return {
        "status": "evaluated",
        "score": score,
        "selected": selected,
        "candidate_count": len(ranked),
        "ranked": ranked,
        "learning_candidate": score >= 0.65,
    }
