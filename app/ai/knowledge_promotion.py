"""Guarded promotion from candidate claims to trusted knowledge."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class PromotionDecision:
    status: str
    score: float
    reasons: List[str] = field(default_factory=list)


class KnowledgePromotion:
    """Separates repeated opinions from independently corroborated evidence."""

    def evaluate(
        self,
        source_weights: List[float],
        independent_groups: int,
        verified_successes: int,
        conflicts: int = 0,
    ) -> PromotionDecision:
        reasons: List[str] = []
        if conflicts:
            return PromotionDecision("blocked", 0.0, ["conflicting evidence"])
        if not source_weights or independent_groups < 2:
            return PromotionDecision("candidate", 0.0, ["insufficient independent evidence"])
        source_score = min(1.0, sum(sorted(source_weights, reverse=True)[:3]) / 2.0)
        verification_score = min(1.0, verified_successes / 2.0)
        score = round(0.55 * source_score + 0.45 * verification_score, 4)
        if verified_successes >= 2 and independent_groups >= 2 and score >= 0.75:
            reasons.append("independent evidence and repeated verification")
            return PromotionDecision("trusted", score, reasons)
        reasons.append("more evidence or verification required")
        return PromotionDecision("candidate", score, reasons)
