"""Bridge between Bitey channels and an external AI rector.

Bitey is the communication medium, context carrier, memory and apprentice.
It does not cognitively evaluate or choose the external AI's answer.
"""
from typing import Any, Dict

from app.ai.ai_council import consult
from app.ai.learning_candidates import record_candidate
from app.ai.web_intelligence import needs_web, search_web
from app.ai.web_learning import record_web_candidate


def _research_query(message: str, context: Dict[str, Any], intent_name: str | None) -> str:
    """Expand a short follow-up into a context-aware research query.

    The user's wording remains the primary query. Active conversation state is
    only added when it makes the research target unambiguous, preventing
    searches such as "how much?" from losing the object being discussed.
    """
    state = context.get("contextual_state") or {}
    conversation = context.get("conversation") or {}
    candidates = [
        state.get("active_topic"),
        state.get("active_object"),
        state.get("active_problem"),
        state.get("active_service"),
        conversation.get("active_topic"),
        conversation.get("active_object"),
        conversation.get("active_problem"),
        context.get("last_service"),
    ]
    anchors = []
    for value in candidates:
        if isinstance(value, dict):
            value = value.get("name") or value.get("title") or value.get("slug")
        value = str(value or "").strip()
        if value and value not in anchors:
            anchors.append(value)
    if intent_name and intent_name not in anchors:
        anchors.append(intent_name)
    base = " ".join(str(message or "").strip().split())
    if not base:
        return ""
    # Do not bloat already-specific queries. Add at most two contextual anchors.
    if len(base.split()) >= 8:
        return base
    return " ".join(anchors[:2] + [base]) if anchors else base


def consult_if_valuable(*, company_id: int, message: str, language: str, intent: Dict[str, Any], context: Dict[str, Any], conversation_id: Any = None) -> Dict[str, Any]:
    """Transport bounded enterprise context to one external cognitive rector."""
    intent_name = intent.get("intent")
    knowledge_found = not bool(context.get("knowledge_gap", 0))

    web = {"used": False, "grounding_status": "not_needed", "results": [], "queries": []}
    research_query = _research_query(message, context, intent_name)
    if needs_web(message, intent=intent_name, knowledge_found=knowledge_found):
        web = search_web(research_query or message, intent=intent_name, company_id=company_id)
        if web.get("learning_candidate"):
            record_web_candidate(company_id=company_id, message=message, web=web, conversation_id=conversation_id)

    # The research layer already produces scored/verified sources. Preserve the
    # original company knowledge and add web grounding as an evidence section so
    # the external rector actually receives the research it is expected to use.
    enriched_knowledge = {
        "company_knowledge": context.get("knowledge"),
        "web_grounding": web,
    }
    enriched_context = {
        **context,
        "knowledge": enriched_knowledge,
        "web_grounding": web,
        "research_query": research_query,
        "cognitive_authority": "external_ai",
        "bitey_role": "communication_context_memory_apprentice_tools_persistence",
        "bitey_decision_authority": False,
        "learning_authority": "external_ai",
    }

    # max_providers=1 means one external AI owns the cognitive turn.
    # Failover inside consult is operational only: if the first provider is
    # unavailable, the next external provider receives the same cognitive turn.
    results = consult(message, language=language, context=enriched_context, max_providers=1)

    if not results:
        return {
            "used": False,
            "reason": "no_external_ai_response",
            "suggestions": [],
            "web_grounding": web,
            "research_query": research_query,
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
        "research_query": research_query,
        "process": [
            "channel_input",
            "context_and_memory_transport",
            "context_aware_research_query",
            "web_research_and_verification",
            "external_ai_cognitive_analysis",
            "external_ai_response",
            "learning_evidence_storage",
            "channel_output",
        ],
    }
