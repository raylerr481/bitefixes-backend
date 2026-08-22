"""External-AI rector gateway.

External AI is the sole cognitive and conversational authority. Bitey supplies
company context, memory, governed tools, persistence and operational safety,
but does not evaluate, rewrite, rank or replace an external-AI answer.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from app.services.company_service import get_company_context
from app.ai.consultation_service import consult_if_valuable


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
    """Prepare context and let the external rector produce the response.

    Bitey does not perform cognitive evaluation of the external response.
    Provider health/failover is infrastructure only; the selected external AI
    remains responsible for interpreting the context and self-checking its own
    answer according to the rector directives.
    """
    context = business_context
    if context is None:
        try:
            context = get_company_context(company_id) or {}
        except Exception as exc:
            print("[AI-FIRST CONTEXT WARNING]", type(exc).__name__)
            context = {}

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
                "architecture": "external-rector-primary-v34",
                "cognitive_authority": "external_ai",
                "bitey_role": "context_memory_tools_persistence_operations",
                "response_authority": selected_provider or "external_ai",
                "external_ai_self_evaluation": True,
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
            "architecture": "external-rector-primary-v34",
            "cognitive_authority": "external_ai_unavailable",
            "bitey_role": "context_memory_tools_persistence_operations",
            "external_ai_self_evaluation": True,
            "action_engine": "deferred",
            "ai_consultation": consultation,
        },
    }
