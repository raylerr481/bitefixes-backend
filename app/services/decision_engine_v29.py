"""External-AI rector gateway.

The Company AI Profile is loaded first and is authoritative for tenant
identity, business context and governance. External AI is the cognitive
authority only after that profile is present and valid.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from app.services.company_service import get_company_context
from app.ai.consultation_service import consult_if_valuable


def _profile_is_valid(context: Dict[str, Any]) -> bool:
    profile_record = context.get("company_ai_profile")
    if not isinstance(profile_record, dict):
        return False
    profile = profile_record.get("profile")
    return bool(
        profile_record.get("authoritative")
        and isinstance(profile, dict)
        and profile
        and profile_record.get("company_id")
    )


def decision_engine(
    company_id: int,
    customer: Dict[str, Any],
    message: str,
    intent: Dict[str, Any],
    knowledge: Any = None,
    memory: Any = None,
    language: Optional[str] = None,
    business_context: Optional[Dict[str, Any]] = None,
):
    """Load authoritative tenant context, then give one cognitive turn to external AI."""
    runtime_context = business_context if isinstance(business_context, dict) else {}
    try:
        authoritative_context = get_company_context(company_id) or {}
    except Exception as exc:
        print("[AI-FIRST CONTEXT WARNING]", type(exc).__name__)
        authoritative_context = {}

    # Never let a conversational/legacy context replace the tenant profile.
    # It may add runtime state, but the persisted Company AI Profile wins.
    context = {**runtime_context, **authoritative_context}
    if runtime_context.get("conversation_id"):
        context["conversation_id"] = runtime_context["conversation_id"]
    if not _profile_is_valid(context):
        return {
            "action": "conversation",
            "create_ticket": False,
            "requires_quote": False,
            "ticket_type": None,
            "response": "No puedo iniciar una respuesta empresarial todavía porque el perfil de contexto de esta empresa no está disponible o no está validado.",
            "workflow": None,
            "service": None,
            "service_id": None,
            "reasoning": {},
            "metadata": {
                "architecture": "company-ai-profile-first-v35",
                "cognitive_authority": "blocked_profile_missing",
                "profile_required": True,
                "action_engine": "deferred",
            },
        }

    memory_dict = memory if isinstance(memory, dict) else {}
    intent_dict = intent if isinstance(intent, dict) else {}
    history = memory_dict.get("history", [])

    consultation = {"used": False, "reason": "not_attempted"}
    try:
        consultation = consult_if_valuable(
            company_id=company_id,
            message=message,
            language=language or "es",
            intent=intent_dict,
            context={
                "company_id": company_id,
                "customer_id": customer.get("id"),
                "business_context": context,
                "company_ai_profile": context.get("company_ai_profile"),
                "memory": memory_dict,
                "history": history,
                "last_service": memory_dict.get("last_service"),
                "knowledge": knowledge,
                "knowledge_gap": 0.0 if knowledge else 0.7,
                "service_id": intent_dict.get("service_id") or memory_dict.get("last_service"),
                "complexity": 0.4,
                "novelty": 0.7 if not intent_dict.get("intent") else 0.25,
                "business_impact": 0.2,
                "estimated_cost": 0.0,
            },
            conversation_id=memory_dict.get("conversation_id"),
        )
    except Exception as exc:
        print("[AI-FIRST CONSULTATION WARNING]", type(exc).__name__)
        consultation = {"used": False, "reason": "consultation_error"}

    answer = str(consultation.get("answer") or "").strip()
    selected_provider = consultation.get("provider")
    if answer:
        return {
            "action": "conversation",
            "create_ticket": False,
            "requires_quote": False,
            "ticket_type": None,
            "response": answer,
            "workflow": None,
            "service": None,
            "service_id": intent_dict.get("service_id") or memory_dict.get("last_service"),
            "reasoning": {},
            "metadata": {
                "architecture": "company-ai-profile-first-v35",
                "cognitive_authority": "external_ai",
                "bitey_role": "authoritative_company_context_memory_tools_persistence_operations",
                "response_authority": selected_provider or "external_ai",
                "external_ai_self_evaluation": True,
                "profile_id": context.get("company_ai_profile", {}).get("id"),
                "action_engine": "deferred",
                "ai_consultation": consultation,
            },
        }

    return {
        "action": "conversation",
        "create_ticket": False,
        "requires_quote": False,
        "ticket_type": None,
        "response": "No pude obtener en este momento una respuesta de la IA rectora. La conversación queda abierta y no se ha creado ningún ticket.",
        "workflow": None,
        "service": None,
        "service_id": None,
        "reasoning": {},
        "metadata": {
            "architecture": "company-ai-profile-first-v35",
            "cognitive_authority": "external_ai_unavailable",
            "bitey_role": "authoritative_company_context_memory_tools_persistence_operations",
            "external_ai_self_evaluation": True,
            "profile_id": context.get("company_ai_profile", {}).get("id"),
            "action_engine": "deferred",
            "ai_consultation": consultation,
        },
    }
