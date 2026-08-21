"""Trust policy for promoting candidate knowledge."""
from typing import Any, Dict


class TrustEngine:
    def evaluate(self, candidate: Dict[str, Any], *, verified: bool, corroborations: int = 0) -> Dict[str, Any]:
        score = 0.25
        score += 0.35 if verified else 0.0
        score += min(0.30, 0.10 * max(0, corroborations))
        score = min(1.0, score)
        return {
            "trust_score": score,
            "status": "trusted" if verified and corroborations >= 2 and score >= 0.80 else "candidate",
            "promotable": bool(verified and corroborations >= 2 and score >= 0.80),
            "candidate": candidate,
        }
