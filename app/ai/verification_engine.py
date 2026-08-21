"""Verification gate before diagnostic knowledge can be promoted."""
from dataclasses import dataclass


@dataclass
class VerificationResult:
    success: bool
    observation: str
    confidence_delta: float
    promotable: bool = False


class VerificationEngine:
    def verify(self, success: bool, observation: str, prior_confidence: float = 0.0) -> VerificationResult:
        delta = 0.20 if success else -0.20
        confidence = max(0.0, min(1.0, prior_confidence + delta))
        return VerificationResult(
            success=success,
            observation=observation,
            confidence_delta=delta,
            promotable=success and confidence >= 0.80,
        )
