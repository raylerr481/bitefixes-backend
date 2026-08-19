"""Decides whether an external AI consultation is justified.

Bitey first attempts deterministic/core reasoning. External AI is a bounded
advisory resource, not the default execution path.
"""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ConsultationDecision:
    consult: bool
    reason: str
    estimated_value: float
    estimated_cost_budget: float
    max_providers: int


def evaluate(*, confidence: float, complexity: float = 0.0, novelty: float = 0.0,
             knowledge_gap: float = 0.0, business_impact: float = 0.0,
             estimated_cost: float = 0.0) -> ConsultationDecision:
    min_conf = float(os.getenv("AI_CONSULT_MIN_CONFIDENCE", "0.78"))
    max_cost = float(os.getenv("AI_CONSULT_MAX_ESTIMATED_COST", "0.01"))
    value = (1-confidence)*0.35 + complexity*0.20 + novelty*0.15 + knowledge_gap*0.20 + business_impact*0.10
    consult = confidence < min_conf and value >= 0.18 and estimated_cost <= max_cost
    reason = "core_sufficient" if confidence >= min_conf else ("cost_guard" if estimated_cost > max_cost else ("low_expected_value" if value < 0.18 else "external_consultation"))
    return ConsultationDecision(consult, reason, round(value, 4), max_cost, int(os.getenv("AI_COUNCIL_MAX_PROVIDERS", "2")))
