"""Bitey V29 AI-first decision gateway.

External AI is the first cognitive authority. The legacy decision engine is
kept as an execution fallback only after the external advisory layer has had
an opportunity to interpret the conversation.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.company_service import get_company_context
from app.services.decision_engine import make_decision as legacy_make_decision
from app.ai.consultation_service import consult_if_valuable


def _selected_answer(consultation: Dict[str, Any]) -> Optional[str]:
    evaluation = consultation.get("evaluation") or {}
    selected = evaluation.get("selected") or {}
    answer = selected.get("answer")
    return str(answer).strip() if answer else None


def _external_stage(consultation: Dict[str, Any], message: str) -> str:
    """Infer only an action-safety stage; never claims Bitey cognitive authority."""
    text = str(message or "").lower()
    explicit_commitment = any(marker in text for marker in (
        "quiero contratar", "quiero contratarlo", "contratar el servicio",
        "deseo contratar", "sí, quiero contratar", "si, quiero contratar",
        "quiero comprar", "i want to hire", "i want to buy",
        "quero contratar", "quero comprar",
    ))
    if explicit_commitment:
        return "commitment_candidate"
    if consultation.get("used"):
        return "conversation_or_diagnostic"
    return "unavailable"


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
    """AI-first routing followed by deterministic action execution.

    The external AI receives the business context, memory, knowledge and tool
    policy first. If it produces a usable advisory answer, ordinary turns are
    returned as conversation/diagnostic turns and cannot create a ticket yet.
    The legacy engine is invoked only when the advisory layer is unavailable,
    or when an explicit commitment candidate allows the action layer to run.
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

    # Keep the external rector first. No ticket/quote/workflow is created by
    # this layer; it only interprets and advises using governed tools.
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
                "history": memory_dict.get("history", []),
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

    answer = _selected_answer(consultation)
    stage = _external_stage(consultation, message)

    if answer and stage != "commitment_candidate":
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
                "architecture": "ai_first_v29",
                "cognitive_authority": "external_ai",
                "bitey_role": "context_memory_learning",
                "conversation_stage": stage,
                "action_engine": "deferred",
                "ai_consultation": consultation,
            },
        }

    # Explicit commitment may proceed to the existing action engine. It is
    # still the executor, not the cognitive authority.
    result = legacy_make_decision(
        company_id,
        customer,
        message,
        intent_dict,
        knowledge,
        memory_dict,
        language,
        business_context=context,
    )
    if isinstance(result, dict):
        metadata = result.setdefault("metadata", {})
        metadata.update({
            "architecture": "ai_first_v29",
            "cognitive_authority": "external_ai" if consultation.get("used") else "fallback",
            "bitey_role": "context_memory_learning",
            "conversation_stage": stage,
            "ai_consultation": consultation,
        })
    return result
