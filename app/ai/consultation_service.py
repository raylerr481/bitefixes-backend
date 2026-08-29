"""Bridge between Bitey channels and an external AI rector.

Bitey is the communication medium, context carrier, memory and apprentice.
It does not cognitively evaluate or choose the external AI's answer.
"""
from typing import Any, Dict

from app.ai.ai_council import consult
from app.ai.contextual_message_resolver import resolve_contextual_message
from app.ai.learning_candidates import record_candidate
from app.ai.web_intelligence import needs_web, search_web
from app.ai.web_learning import record_web_candidate


def _contextual_inputs(context: Dict[str, Any]) -> tuple[list[dict[str, Any]], str | None, str | None, str | None]:
    memory = context.get("memory") or {}
    conversation = context.get("conversation") or {}
    state = context.get("contextual_state") or {}
    profile = context.get("company_ai_profile") or {}
    recent = conversation.get("recent_turns") or memory.get("recent_turns") or context.get("history") or []
    # The active problem is the strongest semantic anchor. A device/model is
    # an attribute of that problem, not a replacement for it.
    entity = (state.get("active_problem") or conversation.get("active_problem") or memory.get("active_problem") or state.get("active_object") or state.get("active_topic") or conversation.get("active_object") or conversation.get("active_topic") or memory.get("active_object") or memory.get("active_topic") or profile.get("company_name"))
    goal = context.get("active_goal") or memory.get("active_goal")
    active_url = memory.get("active_url") or state.get("active_url")
    return recent, entity, goal, active_url


def _research_query(message: str, context: Dict[str, Any], intent_name: str | None) -> str:
    """Expand a short follow-up and preserve an active research subject."""
    state = context.get("contextual_state") or {}
    recent, entity, goal, active_url = _contextual_inputs(context)
    candidates = [state.get("active_problem"), state.get("active_topic"), state.get("active_object"), state.get("active_model"), state.get("active_service"), (context.get("conversation") or {}).get("active_problem"), (context.get("conversation") or {}).get("active_topic"), (context.get("conversation") or {}).get("active_object"), (context.get("conversation") or {}).get("active_model"), (context.get("memory") or {}).get("last_service")]
    anchors = []
    for value in candidates:
        if isinstance(value, dict):
            value = value.get("name") or value.get("title") or value.get("slug") or value.get("problem")
        value = str(value or "").strip()
        if value and value not in anchors:
            anchors.append(value)
    if intent_name and intent_name not in anchors:
        anchors.append(intent_name)
    base = " ".join(str(message or "").strip().split())
    if not base:
        return ""
    resolved = resolve_contextual_message(base, history=recent, active_entity=entity, active_goal=goal)
    base = resolved.get("resolved_message") or base
    if active_url and len(base.split()) <= 8 and active_url not in base:
        base = f"{base} [context_url: {active_url}]"
    if len(base.split()) >= 8:
        return base
    return " ".join(anchors[:2] + [base]) if anchors else base


def consult_if_valuable(*, company_id: int, message: str, language: str, intent: Dict[str, Any], context: Dict[str, Any], conversation_id: Any = None) -> Dict[str, Any]:
    """Transport bounded enterprise context to one external cognitive rector."""
    intent_name = intent.get("intent")
    knowledge_found = not bool(context.get("knowledge_gap", 0))
    recent, entity, goal, active_url = _contextual_inputs(context)
    contextual = resolve_contextual_message(message, history=recent, active_entity=entity, active_goal=goal)

    web = {"used": False, "grounding_status": "not_needed", "results": [], "queries": [], "research_candidate": bool(contextual.get("research_candidate"))}
    research_query = _research_query(message, context, intent_name)
    should_research = contextual.get("research_candidate") or needs_web(message, intent=intent_name, knowledge_found=knowledge_found)
    if should_research:
        web = search_web(research_query or message, intent=intent_name, company_id=company_id)
        web["research_candidate"] = bool(contextual.get("research_candidate"))
        if web.get("learning_candidate"):
            record_web_candidate(company_id=company_id, message=message, web=web, conversation_id=conversation_id)

    enriched_knowledge = {"company_knowledge": context.get("knowledge"), "web_grounding": web}
    enriched_context = {**context, "knowledge": enriched_knowledge, "web_grounding": web, "research_query": research_query, "contextual_resolution": contextual, "cognitive_authority": "external_ai", "bitey_role": "communication_context_memory_apprentice_tools_persistence", "bitey_decision_authority": False, "learning_authority": "external_ai", "continuity_guard": {"active_problem": (context.get("memory") or {}).get("active_problem"), "active_object": (context.get("memory") or {}).get("active_object"), "active_model": (context.get("memory") or {}).get("active_model"), "rule": "A short entity-only follow-up updates the active problem; it never replaces it."}}
    # Give the reasoning model the context-resolved turn, not the isolated
    # entity. This prevents "Redmi 9A" from being interpreted as a new issue.
    effective_message = contextual.get("resolved_message") or message
    results = consult(effective_message, language=language, context=enriched_context, max_providers=1)

    if not results:
        return {"used": False, "reason": "no_external_ai_response", "suggestions": [], "web_grounding": web, "research_query": research_query, "authority": "external_ai", "bitey_role": "communication_medium_and_apprentice"}

    selected = results[0]
    answer = str(selected.get("answer") or "").strip()
    provider = str(selected.get("provider") or "unknown")
    if answer:
        record_candidate(company_id=company_id, message=message, provider=provider, suggestion=selected, evaluation={"authority": "external_ai", "mode": "external_ai_learning_evidence", "bitey_is_apprentice": True, "bitey_has_decision_authority": False}, conversation_id=conversation_id)

    return {"used": bool(answer), "reason": "external_ai_primary", "answer": answer, "provider": provider, "suggestions": results, "selection": {"authority": "external_ai", "mode": "first_healthy_external_ai", "provider": provider}, "web_grounding": web, "research_query": research_query, "contextual_resolution": contextual, "process": ["channel_input", "context_and_memory_transport", "contextual_resolution", "context_aware_research_query", "web_research_and_verification", "external_ai_cognitive_analysis", "external_ai_response", "learning_evidence_storage", "channel_output"]}
