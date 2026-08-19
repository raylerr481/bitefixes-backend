"""Governed semantic learning for Bitey.

New terms/relations are recorded as candidates/observations first. Promotion
to canonical knowledge requires evidence and must never be inferred from a
single untrusted model response.
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class LearningObservation:
    term: str
    concept: str
    confidence: float
    source: str
    provider: str | None = None


def make_observation(
    term: str,
    concept: str,
    *,
    confidence: float,
    source: str,
    provider: str | None = None,
) -> dict[str, Any]:
    confidence = max(0.0, min(1.0, float(confidence)))
    return {
        "term": term.strip(),
        "concept": concept.strip(),
        "confidence": confidence,
        "source": source,
        "provider": provider,
        "status": "candidate" if confidence < 0.95 else "observation",
    }
