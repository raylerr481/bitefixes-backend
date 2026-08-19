"""Single governed entry point for external AI consultation."""
from typing import Any, Dict

from app.ai.consultation_gate import evaluate
from app.ai.ai_council import consult
from app.ai.evaluator_suggestions import evaluate_suggestions
from app.ai.learning_candidates import record_candidate


def consult_if_valuable(
    *,
    company_id: int,
    message: str,
    language: str,
    intent: Dict[str, Any],
    context: Dict[str, Any],
    conversation_id: Any = None,
) -> Dict[str, Any]:
    confidence = float(intent.get("confidence", 0) or 0)
    gate = evaluate(
        confidence=confidence,
        complexity=float(context.get("complexity", 0) or 0),
        novelty=float(context.get("novelty", 0) or 0),
        knowledge_gap=float(context.get("knowledge_gap", 0) or 0),
        business_impact=float(context.get("business_impact", 0) or 0),
        estimated_cost=float(context.get("estimated_cost", 0) or 0),
    )
    if not gate.consult:
        return {"used": False, "reason": gate.reason, "gate": gate.__dict__}

    suggestions = consult(
        message,
        language=language,
        context=context,
        max_providers=gate.max_providers,
    )
    evaluation = evaluate_suggestions(suggestions, core_confidence=confidence)

    if evaluation.get("learning_candidate") and evaluation.get("selected"):
        selected = evaluation["selected"]
        record_candidate(
            company_id=company_id,
            message=message,
            provider=selected.get("provider", "unknown"),
            suggestion=selected,
            evaluation=evaluation,
            conversation_id=conversation_id,
        )

    return {
        "used": bool(suggestions),
        "gate": gate.__dict__,
        "suggestions": suggestions,
        "evaluation": evaluation,
    }
