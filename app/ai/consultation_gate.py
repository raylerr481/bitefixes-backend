"""Decides whether an external AI consultation is justified.

Bitey Core remains the authority. External AI is an advisory source selected
when it can materially improve an answer, especially for procedural, novel,
troubleshooting and knowledge-gap questions.
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
             estimated_cost: float = 0.0, force_advisory: bool = False,
             advisory_reason: str = "") -> ConsultationDecision:
    min_conf = float(os.getenv("AI_CONSULT_MIN_CONFIDENCE", "0.78"))
    max_cost = float(os.getenv("AI_CONSULT_MAX_ESTIMATED_COST", "0.01"))
    value = (1-confidence)*0.30 + complexity*0.20 + novelty*0.20 + knowledge_gap*0.20 + business_impact*0.10
    cost_allowed = estimated_cost <= max_cost

    # A high core confidence must not suppress a useful second opinion when the
    # user explicitly asks how to perform a repair/procedure or when the question
    # is troubleshooting/novel. The advisory call remains bounded by cost.
    consult = cost_allowed and (force_advisory or (confidence < min_conf and value >= 0.18))

    if not cost_allowed:
        reason = "cost_guard"
    elif force_advisory:
        reason = advisory_reason or "procedural_advisory"
    elif confidence >= min_conf:
        reason = "core_sufficient"
    elif value < 0.18:
        reason = "low_expected_value"
    else:
        reason = "external_consultation"

    return ConsultationDecision(
        consult=consult,
        reason=reason,
        estimated_value=round(value, 4),
        estimated_cost_budget=max_cost,
        max_providers=int(os.getenv("AI_COUNCIL_MAX_PROVIDERS", "2")),
    )
