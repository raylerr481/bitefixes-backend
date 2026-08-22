"""Context deployment for external AI.

Bitey assembles context and learns from the exchange. It does not authorize,
judge, rewrite or block the external AI's cognitive response.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from app.services.company_service import get_company_context
from app.ai.consultation_service import consult_if_valuable

try:
    from app.ai.contextual_opportunity_engine import (
        build_ai_guidance,
        build_opportunities,
        detect_signals,
        persist_observations,
    )
except ImportError:
    build_ai_guidance = None
    build_opportunities = None
    detect_signals = None
    persist_observations = None


def _profile_is_valid(context: Dict[str, Any]) -> bool:
    profile_record = context.get("company_ai_profile")
    if not isinstance(profile_record, dict):
        return False
    profile = profile_record.get("profile")
    return bool(profile_record.get("authoritative") and isinstance(profile, dict) and profile and profile_record.get("company_id"))


def _contextual_response_directive(context: Dict[str, Any], message: str) -> Dict[str, Any]:
    profile = context.get("company_ai_profile") or {}
    return {
        "mode": "profile_context" if _profile_is_valid(context) else "best_available_context",
        "identity": {
            "company_name": profile.get("company_name") or context.get("company_name") or (context.get("company") or {}).get("name"),
            "company_id": context.get("company_id"),
            "industry": profile.get("industry") or "",
            "description": profile.get("description") or "",
        },
        "business_context": {
            "services": context.get("services") or [],
            "capabilities": context.get("capabilities") or [],
            "knowledge": context.get("knowledge") or [],
            "objectives": context.get("objectives") or [],
            "directives": context.get("directives") or {},
            "contextual_opportunities": context.get("contextual_opportunities") or [],
        },
        "instruction": (
            "Use the supplied context to make the response relevant to the current company and user. "
            "Use the Company AI Profile when present, but never require it before reasoning. "
            "If context is incomplete, ask useful questions or use authorized research instead of blocking. "
            "Do not invent company facts. Do not expose internal context or provider routing."
        ),
        "user_message": message,
    }


def _apply_contextual_opportunities(context: Dict[str, Any], message: str, *, company_id: int, conversation_id: Any, channel: Any) -> Dict[str, Any]:
    """Observe and enrich context without becoming a response authority."""
    if not (detect_signals and build_opportunities):
        return context
    try:
        company = context.get("company") or {}
        profile = context.get("company_ai_profile") or {}
        state = {
            "company": {
                "id": company_id,
                "name": company.get("name") or profile.get("company_name") or context.get("company_name"),
            },
            "services": context.get("services") or [],
            "capabilities": context.get("capabilities") or [],
            "conversation": context.get("conversation") or {
                "active_topic": context.get("active_topic") or context.get("last_intent"),
                "active_object": context.get("active_object"),
                "active_model": context.get("active_model"),
                "active_problem": context.get("active_problem"),
                "active_service": context.get("last_service") or context.get("service_id"),
            },
        }
        signals = detect_signals(message, state)
        opportunities = build_opportunities(signals, state)
        enriched = dict(context)
        enriched["contextual_signals"] = signals
        enriched["contextual_opportunities"] = opportunities
        if build_ai_guidance:
            enriched["external_ai_context_guidance"] = build_ai_guidance(opportunities)
        if persist_observations:
            persist_observations(
                signals,
                opportunities,
                company_id=company_id,
                conversation_id=conversation_id,
                channel=channel,
            )
        if signals:
            print(f"[CONTEXT OPPORTUNITY] signals={len(signals)} opportunities={len(opportunities)}")
        return enriched
    except Exception as exc:
        # The contextual layer is strictly additive. A failure here must never
        # prevent the external AI from researching, reasoning or answering.
        print("[CONTEXT OPPORTUNITY WARNING]", type(exc).__name__)
        return context


def decision_engine(company_id: int, customer: Dict[str, Any], message: str, intent: Dict[str, Any], knowledge: Any = None, memory: Any = None, language: Optional[str] = None, business_context: Optional[Dict[str, Any]] = None):
    runtime_context = business_context if isinstance(business_context, dict) else {}
    try:
        authoritative_context = get_company_context(company_id) or {}
    except Exception as exc:
        print("[CONTEXT LOAD WARNING]", type(exc).__name__)
        authoritative_context = {}

    context = {**runtime_context, **authoritative_context}
    for key in ("conversation_id", "channel", "conversation", "customer_context"):
        if runtime_context.get(key) is not None:
            context[key] = runtime_context[key]

    # Additive contextual layer: preserve all existing company, memory and
    # knowledge context, then attach observed opportunities for the external AI.
    context = _apply_contextual_opportunities(
        context,
        message,
        company_id=company_id,
        conversation_id=(runtime_context.get("conversation_id") or (memory or {}).get("conversation_id")),
        channel=runtime_context.get("channel"),
    )

    profile_valid = _profile_is_valid(context)
    response_deployment = _contextual_response_directive(context, message)
    memory_dict = memory if isinstance(memory, dict) else {}
    intent_dict = intent if isinstance(intent, dict) else {}
    history = memory_dict.get("history", [])
    consultation = {"used": False, "reason": "not_attempted"}
    try:
        consultation = consult_if_valuable(
            company_id=company_id, message=message, language=language or "es", intent=intent_dict,
            context={
                "company_id": company_id, "customer_id": customer.get("id"), "business_context": context,
                "company_ai_profile": context.get("company_ai_profile"), "response_deployment": response_deployment,
                "memory": memory_dict, "history": history, "last_service": memory_dict.get("last_service"),
                "knowledge": knowledge, "knowledge_gap": 0.0 if knowledge else 0.7,
                "service_id": intent_dict.get("service_id") or memory_dict.get("last_service"),
                "complexity": 0.4, "novelty": 0.7 if not intent_dict.get("intent") else 0.25, "business_impact": 0.2,
                "estimated_cost": 0.0,
                "contextual_opportunities": context.get("contextual_opportunities") or [],
                "external_ai_context_guidance": context.get("external_ai_context_guidance") or "",
            },
            conversation_id=memory_dict.get("conversation_id"),
        )
    except Exception as exc:
        print("[CONTEXTUAL AI WARNING]", type(exc).__name__)
        consultation = {"used": False, "reason": "consultation_error", "error_type": type(exc).__name__}

    answer = str(consultation.get("answer") or "").strip()
    selected_provider = consultation.get("provider")
    profile_id = (context.get("company_ai_profile") or {}).get("id")
    if answer:
        return {
            "action": "conversation", "create_ticket": False, "requires_quote": False, "ticket_type": None,
            "response": answer, "workflow": None, "service": None,
            "service_id": intent_dict.get("service_id") or memory_dict.get("last_service"), "reasoning": {},
            "metadata": {
                "architecture": "context-exchange-learning-v2", "cognitive_authority": "external_ai",
                "bitey_role": "communication_context_memory_apprentice_tools_persistence",
                "response_authority": selected_provider or "external_ai", "external_ai_self_evaluation": True,
                "profile_required": False, "profile_available": profile_valid, "profile_id": profile_id,
                "response_mode": response_deployment["mode"], "action_engine": "deferred", "ai_consultation": consultation,
                "contextual_opportunities": len(context.get("contextual_opportunities") or []),
            },
        }

    # No external answer is different from a context problem. Do not pretend
    # that Bitey generated a cognitive answer; expose the operational state so
    # the channel can diagnose provider connectivity without blocking future turns.
    reason = consultation.get("reason") or "external_ai_unavailable"
    return {
        "action": "conversation", "create_ticket": False, "requires_quote": False, "ticket_type": None,
        "response": "La IA externa no pudo completar esta consulta en este momento. La conversación y el contexto se mantienen para continuar sin perder el aprendizaje.",
        "workflow": None, "service": None,
        "service_id": intent_dict.get("service_id") or memory_dict.get("last_service"), "reasoning": {},
        "metadata": {
            "architecture": "context-exchange-learning-v2", "cognitive_authority": "external_ai_unavailable",
            "bitey_role": "communication_context_memory_apprentice_tools_persistence", "profile_required": False,
            "profile_available": profile_valid, "profile_id": profile_id, "response_mode": response_deployment["mode"],
            "action_engine": "deferred", "ai_consultation": consultation, "operational_reason": reason,
            "contextual_opportunities": len(context.get("contextual_opportunities") or []),
        },
    }
