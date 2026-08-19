"""Safe evaluation helpers for multi-model answers."""
from typing import Any


def evaluate_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Return consensus metadata without treating model output as truth.

    A candidate is only an observation. Business actions must still be decided
    by Bitey Core/workflows.
    """
    valid = [c for c in candidates if c.get("answer")]
    if not valid:
        return {"status": "no_candidates", "confidence": 0.0, "consensus": None}

    answers = [str(c["answer"]).strip() for c in valid]
    unique = list(dict.fromkeys(answers))
    agreement = 1.0 if len(unique) == 1 else len(valid) / (len(valid) + len(unique))
    return {
        "status": "evaluated",
        "confidence": round(agreement, 3),
        "consensus": unique[0] if len(unique) == 1 else None,
        "candidate_count": len(valid),
    }
