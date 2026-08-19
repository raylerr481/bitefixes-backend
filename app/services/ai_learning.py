"""Learning boundary: external answers become candidates, never trusted facts."""
from __future__ import annotations

from typing import Any


def build_learning_candidate(question: str, council_result: dict[str, Any], context: dict[str, Any]) -> dict[str, Any] | None:
    if not council_result.get("learning_candidate"):
        return None
    answers = council_result.get("answers") or []
    if not answers:
        return None
    return {
        "question": question,
        "context": context,
        "answers": answers,
        "agreement_score": council_result.get("agreement_score", 0.0),
        "status": "pending_verification",
    }
