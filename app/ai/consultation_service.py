"""Single governed entry point for external AI and web consultation."""
from typing import Any, Dict

from app.ai.consultation_gate import evaluate
from app.ai.ai_council import consult
from app.ai.evaluator_suggestions import evaluate_suggestions
from app.ai.learning_candidates import record_candidate
from app.ai.web_intelligence import needs_web, search_web
from app.ai.web_learning import record_web_candidate


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
    intent_name = intent.get("intent")
    knowledge_found = not bool(context.get("knowledge_gap", 0))

    # Web retrieval is memory-first. A fresh Bitey web-memory hit avoids a new
    # external search; current-sensitive questions bypass memory and refresh.
    web = {"used": False, "grounding_status": "not_needed", "results": [], "queries": []}
    if needs_web(message, intent=intent_name, knowledge_found=knowledge_found):
        web = search_web(message, intent=intent_name, company_id=company_id)
        if web.get("learning_candidate"):
            record_web_candidate(
                company_id=company_id,
                message=message,
                web=web,
                conversation_id=conversation_id,
            )

    gate = evaluate(
        confidence=confidence,
        complexity=float(context.get("complexity", 0) or 0),
        novelty=float(context.get("novelty", 0) or 0),
        knowledge_gap=float(context.get("knowledge_gap", 0) or 0),
        business_impact=float(context.get("business_impact", 0) or 0),
        estimated_cost=float(context.get("estimated_cost", 0) or 0),
    )

    # A verified/fresh web-memory answer is already a grounded advisory source.
    # We still let the AI council run when the gate says the reasoning problem is
    # complex; the council receives the memory context and does not own actions.
    if not gate.consult and web.get("used"):
        return {
            "used": False,
            "reason": gate.reason,
            "gate": gate.__dict__,
            "suggestions": [],
            "web_grounding": web,
        }

    if not gate.consult:
        return {
            "used": False,
            "reason": gate.reason,
            "gate": gate.__dict__,
            "web_grounding": web,
        }

    enriched_context = {**context, "web_grounding": web}
    suggestions = consult(
        message,
        language=language,
        context=enriched_context,
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
        "web_grounding": web,
    }
