"""Evidence thresholds for semantic learning."""
from collections import defaultdict
from typing import Any


class SemanticLearningPolicy:
    def __init__(self, promote_threshold: float = 0.97, min_evidence: int = 5) -> None:
        self.promote_threshold = promote_threshold
        self.min_evidence = min_evidence
        self._evidence: dict[tuple[str, str], list[float]] = defaultdict(list)

    def observe(self, term: str, concept: str, confidence: float) -> dict[str, Any]:
        key = (term.strip().lower(), concept.strip().lower())
        self._evidence[key].append(max(0.0, min(1.0, confidence)))
        values = self._evidence[key]
        score = sum(values) / len(values)
        return {
            "term": key[0],
            "concept": key[1],
            "evidence_count": len(values),
            "confidence": round(score, 3),
            "status": (
                "promote"
                if len(values) >= self.min_evidence and score >= self.promote_threshold
                else "candidate"
            ),
        }
