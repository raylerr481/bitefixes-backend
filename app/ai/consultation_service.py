"""Bridge between Bitey channels and an external AI rector.

Bitey is the communication medium, context carrier, memory and apprentice.
It does not cognitively evaluate or choose the external AI's answer.
"""
from typing import Any, Dict

from app.ai.ai_council import consult
from app.ai.learning_candidates import record_candidate
from app.ai.web_intelligence import needs_web, search_web
from app.ai.web_learning import record_web_candidate


def consult_if_valuable(*, company_id: int, message: str, language: str, intent: Dict[str, Any], context: Dict[str, Any], conversation_id: Any = None) -> Dict[str, Any]:
    """Transport bounded enterprise context to one external cognitive rector."""
    intent_name = intent.get("intent")
    knowledge_found = not bool(context.get("knowledge_gap", 0))

    web = {"used": False, "grounding_status": "not_needed", "results": [], "queries": []}
    if needs_web(message, intent=intent_name, knowledge_found=knowledge_found):
        web = search_web(message, intent=intent_name, company_id=company_id)
        if web.get("learning_candidate"):
            record_web_candidate(company_id=company_id, message=message, web=web, conversation_id=conversation_id)

    enriched_context = {
        **context,
        "web_grounding": web,
        "cognitive_authority": "external_ai",
        "bitey_role": "communication_context_memory_apprentice_tools_persistence",
        "bitey_decision_authority": False,
        "learning_authority": "external_ai",
    }

    # max_providers=1 means one external AI owns the cognitive turn.
    # Failover inside consult is operational only: if the first provider is
    # unavailable, the next external provider receives the same cognitive turn.
    results = consult(message, language=language, context=enriched_context, max_providers=1)
    interaction_id = str(conversation_id or context.get("conversation_id") or "unknown")

    if not results:
        return {
            "used": False,
            "reason": "no_external_ai_response",
            "suggestions": [],
            "web_grounding": web,
            "authority": "external_ai",
            "bitey_role": "communication_medium_and_apprentice",
        }

    selected = results[0]
    answer = str(selected.get("answer") or "").strip()
    provider = str(selected.get("provider") or "unknown")

    if answer:
        # Learning evidence is explicitly attributed to the external AI.
        # This is storage for future training; it is not a Bitey evaluation.
        record_candidate(
            company_id=company_id,
            message=message,
            provider=provider,
            suggestion=selected,
            evaluation={
                "authority": "external_ai",
                "mode": "external_ai_learning_evidence",
                "bitey_is_apprentice": True,
                "bitey_has_decision_authority": False,
            },
            conversation_id=conversation_id,
        )

    return {
        "used": bool(answer),
        "reason": "external_ai_primary",
        "answer": answer,
        "provider": provider,
        "suggestions": results,
        "selection": {
            "authority": "external_ai",
            "mode": "first_healthy_external_ai",
            "provider": provider,
        },
        "web_grounding": web,
        "process": [
            "channel_input",
            "context_and_memory_transport",
            "external_ai_cognitive_analysis",
            "external_ai_response",
            "learning_evidence_storage",
            "channel_output",
        ],
    }
