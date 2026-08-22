"""External-AI rector service.

External AI is the cognitive authority. Bitey prepares company context, memory,
web evidence and tools, then gives the cognitive turn to an external provider.
Bitey never scores, ranks, rewrites, vetoes, or judges the provider response.
Any future cognitive/training assessment of Bitey's behavior must be performed
by an external AI and stored as training evidence, not by Bitey's own evaluator.
"""
from typing import Any, Dict

from app.ai.ai_council import consult
from app.ai.learning_candidates import record_candidate
from app.ai.web_intelligence import needs_web, search_web
from app.ai.web_learning import record_web_candidate
from app.ai.evaluation_store import record_provider_evaluation


def consult_if_valuable(*, company_id: int, message: str, language: str, intent: Dict[str, Any], context: Dict[str, Any], conversation_id: Any = None) -> Dict[str, Any]:
    """Give the first cognitive turn directly to an external AI rector."""
    intent_name = intent.get("intent")
    knowledge_found = not bool(context.get("knowledge_gap", 0))

    web = {"used": False, "grounding_status": "not_needed", "results": [], "queries": []}
    if needs_web(message, intent=intent_name, knowledge_found=knowledge_found):
        web = search_web(message, intent=intent_name, company_id=company_id)
        if web.get("learning_candidate"):
            record_web_candidate(company_id=company_id, message=message, web=web, conversation_id=conversation_id)

    # No Bitey cognitive gate, confidence gate, evaluator, ranker or veto.
    # Bitey only supplies bounded enterprise context and operational evidence.
    enriched_context = {
        **context,
        "web_grounding": web,
        "cognitive_authority": "external_ai",
        "response_evaluation_authority": "external_ai",
        "bitey_role": "context_memory_tools_persistence",
    }

    # One external rector owns this interaction. Failover remains inside the
    # provider layer, but Bitey never compares the resulting answers.
    suggestions = consult(message, language=language, context=enriched_context, max_providers=1)
    interaction_id = str(conversation_id or context.get("conversation_id") or "unknown")

    if not suggestions:
        return {
            "used": False,
            "reason": "no_external_ai_response",
            "suggestions": [],
            "web_grounding": web,
            "authority": "external_ai",
        }

    selected = suggestions[0]
    answer = str(selected.get("answer") or "").strip()
    provider = str(selected.get("provider") or "unknown")

    if answer:
        # Telemetry only. This record is not a quality judgment by Bitey.
        record_provider_evaluation(
            company_id=company_id,
            interaction_id=interaction_id,
            provider=provider,
            task_type=str(intent_name or "general_reasoning"),
            answer=answer,
            context={
                **enriched_context,
                "evaluation_authority": "external_ai",
                "telemetry_only": True,
            },
        )
        record_candidate(
            company_id=company_id,
            message=message,
            provider=provider,
            suggestion=selected,
            evaluation={"authority": "external_ai", "mode": "provider_owned"},
            conversation_id=conversation_id,
        )

    return {
        "used": bool(answer),
        "reason": "external_ai_primary",
        "answer": answer,
        "provider": provider,
        "suggestions": suggestions,
        "selection": {
            "authority": "external_ai",
            "mode": "first_healthy_provider",
            "provider": provider,
        },
        "web_grounding": web,
        "process": [
            "context_preparation",
            "external_ai_consultation",
            "provider_health",
            "provider_telemetry",
            "external_ai_cognitive_authority",
        ],
    }
