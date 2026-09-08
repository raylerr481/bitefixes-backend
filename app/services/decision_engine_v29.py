"""Context deployment for external AI plus a bounded local fallback.

Bitey keeps one response authority. External AI is preferred; Bitey Core is
used only when external providers cannot return a usable answer. Enterprise
context is supplied only for conversations that have that context.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from app.services.company_service import get_company_context
from app.ai.consultation_service import consult_if_valuable
from app.ai.bitey_core_fallback import fallback_answer

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


def _conversation_problem_context(context: Dict[str, Any]) -> Dict[str, Any]:
    problem = context.get("problem") if isinstance(context.get("problem"), dict) else {}
    entities = problem.get("entities") if isinstance(problem.get("entities"), dict) else context.get("problem_entities")
    if not isinstance(entities, dict):
        entities = {}
    return {
        "state": problem.get("state") or context.get("problem_state"),
        "is_new": problem.get("is_new") if "is_new" in problem else context.get("problem_is_new"),
        "category": problem.get("category") or context.get("problem_category") or context.get("last_problem"),
        "intent": problem.get("intent") or context.get("last_intent"),
        "device": problem.get("device") or context.get("last_device"),
        "device_kind": problem.get("device_kind"),
        "platform": problem.get("platform") or context.get("last_platform"),
        "os_version": problem.get("os_version") or context.get("last_os_version") or entities.get("os_version"),
        "fingerprint": problem.get("fingerprint") or context.get("last_problem_fingerprint"),
        "entities": entities,
        "coherence": problem.get("coherence") if isinstance(problem.get("coherence"), dict) else {},
    }


def _contextual_response_directive(context: Dict[str, Any], message: str, *, apply_business_context: bool) -> Dict[str, Any]:
    profile = context.get("company_ai_profile") or {}
    if not apply_business_context:
        return {
            "mode": "general_ai",
            "identity": {},
            "business_context": {},
            "conversation_context": {
                "active_problem": _conversation_problem_context(context),
                "history_available": bool(context.get("history")),
            },
            "instruction": (
                "Treat this as a general Bitey IA conversation. Do not inject company identity, services, "
                "objectives or internal business knowledge unless the user explicitly enters a company/service context. "
                "Preserve only relevant conversational continuity and never expose internal routing."
            ),
            "user_message": message,
        }
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
        "conversation_context": {
            "active_problem": _conversation_problem_context(context),
            "last_intent": context.get("last_intent"),
            "last_service": context.get("last_service"),
            "last_ticket": context.get("last_ticket"),
            "history_available": bool(context.get("history")),
        },
        "instruction": (
            "Use the supplied business context only because the current conversation is in a business/service scope. "
            "Preserve the active problem when the current message is a continuation or entity update. "
            "If the user only supplies a detail such as an OS version, acknowledge it as an update and do not restart. "
            "Use the Company AI Profile when present, but never require it before reasoning. Do not invent company facts."
        ),
        "user_message": message,
    }


def _apply_contextual_opportunities(context: Dict[str, Any], message: str, *, company_id: int, conversation_id: Any, channel: Any) -> Dict[str, Any]:
    if not (detect_signals and build_opportunities):
        return context
    try:
        company = context.get("company") or {}
        profile = context.get("company_ai_profile") or {}
        state = {
            "company": {"id": company_id, "name": company.get("name") or profile.get("company_name") or context.get("company_name")},
            "services": context.get("services") or [],
            "capabilities": context.get("capabilities") or [],
            "conversation": context.get("conversation") or {
                "active_topic": context.get("active_topic") or context.get("last_intent"),
                "active_object": context.get("active_object"),
                "active_model": context.get("active_model"),
                "active_problem": context.get("active_problem") or _conversation_problem_context(context),
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
            persist_observations(signals, opportunities, company_id=company_id, conversation_id=conversation_id, channel=channel)
        return enriched
    except Exception as exc:
        print("[CONTEXT OPPORTUNITY WARNING]", type(exc).__name__)
        return context


def _business_context_relevant(message: str, context: Dict[str, Any], intent: Dict[str, Any], memory: Dict[str, Any]) -> bool:
    """Gate enterprise context; general Web questions stay general."""
    m = str(message or "").lower()
    markers = ("bitefix", "ticket", "cliente", "servicio", "presupuesto", "cotización", "cotizacion", "repar", "instal", "impresora", "computadora", "ordenador", "pc", "laptop", "cctv", "cámara", "camara", "wifi", "red", "celular", "móvil", "movil")
    explicit = bool(intent.get("service_id") or memory.get("last_service") or context.get("active_problem") or context.get("problem"))
    return explicit or any(x in m for x in markers)


def decision_engine(company_id: int, customer: Dict[str, Any], message: str, intent: Dict[str, Any], knowledge: Any = None, memory: Any = None, language: Optional[str] = None, business_context: Optional[Dict[str, Any]] = None):
    runtime_context = business_context if isinstance(business_context, dict) else {}
    try:
        authoritative_context = get_company_context(company_id) or {}
    except Exception as exc:
        print("[CONTEXT LOAD WARNING]", type(exc).__name__)
        authoritative_context = {}

    memory_dict = memory if isinstance(memory, dict) else {}
    intent_dict = intent if isinstance(intent, dict) else {}
    context = {**runtime_context, **authoritative_context}
    for key in ("conversation_id", "channel", "conversation", "customer_context", "problem", "problem_state", "problem_is_new", "problem_category", "problem_fingerprint", "last_problem", "last_device", "last_platform", "last_os_version", "problem_entities", "active_problem"):
        if runtime_context.get(key) is not None:
            context[key] = runtime_context[key]

    business_relevant = _business_context_relevant(message, context, intent_dict, memory_dict)
    if not business_relevant:
        # Prevent company context from leaking into a general Bitey IA Web turn.
        context = {k: v for k, v in context.items() if k not in {"company_ai_profile", "company", "company_name", "services", "capabilities", "knowledge", "objectives", "directives", "contextual_opportunities"}}

    context = _apply_contextual_opportunities(
        context, message, company_id=company_id,
        conversation_id=(runtime_context.get("conversation_id") or memory_dict.get("conversation_id")),
        channel=runtime_context.get("channel"),
    ) if business_relevant else context

    profile_valid = _profile_is_valid(context)
    response_deployment = _contextual_response_directive(context, message, apply_business_context=business_relevant)
    history = memory_dict.get("history", [])
    consultation = {"used": False, "reason": "not_attempted"}
    try:
        consultation = consult_if_valuable(
            company_id=company_id, message=message, language=language or "es", intent=intent_dict,
            context={
                "company_id": company_id if business_relevant else None,
                "customer_id": customer.get("id"),
                "business_context": context if business_relevant else {},
                "company_ai_profile": context.get("company_ai_profile") if business_relevant else None,
                "response_deployment": response_deployment,
                "conversation_problem": _conversation_problem_context(context),
                "memory": memory_dict, "history": history,
                "last_service": memory_dict.get("last_service") if business_relevant else None,
                "knowledge": knowledge if business_relevant else None,
                "knowledge_gap": 0.0 if knowledge else 0.7,
                "service_id": intent_dict.get("service_id") or (memory_dict.get("last_service") if business_relevant else None),
                "complexity": 0.4, "novelty": 0.7 if not intent_dict.get("intent") else 0.25,
                "business_impact": 0.2, "estimated_cost": 0.0,
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
    profile_id = (context.get("company_ai_profile") or {}).get("id") if business_relevant else None
    if answer:
        return {
            "action": "conversation", "create_ticket": False, "requires_quote": False, "ticket_type": None,
            "response": answer, "workflow": None, "service": None,
            "service_id": intent_dict.get("service_id") or (memory_dict.get("last_service") if business_relevant else None), "reasoning": {},
            "metadata": {
                "architecture": "bitey-unified-general-plus-business-v1", "cognitive_authority": "external_ai",
                "response_authority": selected_provider or "external_ai", "profile_required": False,
                "profile_available": profile_valid, "profile_id": profile_id, "business_context_applied": business_relevant,
                "response_mode": response_deployment["mode"], "ai_consultation": consultation,
                "contextual_opportunities": len(context.get("contextual_opportunities") or []),
                "active_problem_state": _conversation_problem_context(context),
            },
        }

    # Last resort: deterministic Bitey Core. It is deliberately bounded and never claims to be an LLM.
    local = fallback_answer(message, language=language or "es", context={
        **context,
        "conversation_problem": _conversation_problem_context(context),
        "contextual_state": _conversation_problem_context(context),
    })
    if local:
        return {
            "action": "conversation", "create_ticket": False, "requires_quote": False, "ticket_type": None,
            "response": local["answer"], "workflow": None, "service": None,
            "service_id": intent_dict.get("service_id") or (memory_dict.get("last_service") if business_relevant else None), "reasoning": {},
            "metadata": {
                "architecture": "bitey-unified-general-plus-business-v1", "cognitive_authority": "bitey_core_local",
                "response_authority": "bitey-core-local", "business_context_applied": business_relevant,
                "external_ai_attempt": consultation, "fallback_mode": local.get("mode"),
                "profile_available": profile_valid, "profile_id": profile_id,
                "active_problem_state": _conversation_problem_context(context),
            },
        }

    return {
        "action": "conversation", "create_ticket": False, "requires_quote": False, "ticket_type": None,
        "response": "No pude completar esta respuesta con los proveedores externos disponibles. Mantengo la conversación y el contexto para continuar sin reiniciar.",
        "workflow": None, "service": None,
        "service_id": intent_dict.get("service_id") or (memory_dict.get("last_service") if business_relevant else None), "reasoning": {},
        "metadata": {
            "architecture": "bitey-unified-general-plus-business-v1", "cognitive_authority": "unavailable",
            "response_authority": "none", "business_context_applied": business_relevant,
            "external_ai_attempt": consultation, "profile_available": profile_valid,
            "profile_id": profile_id, "active_problem_state": _conversation_problem_context(context),
        },
    }
