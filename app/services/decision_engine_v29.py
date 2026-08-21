"""Bitey AI-first decision gateway with a cognitive scaffolding layer.

External AI remains the cognitive authority. Bitey's archetypes prepare
context, resolve references, identify needs, choose missing information and
gate actions; they do not replace model reasoning.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.company_service import get_company_context
from app.services.decision_engine import make_decision as legacy_make_decision
from app.ai.consultation_service import consult_if_valuable
from app.cognitive.archetypes import build_cognitive_state, evaluate_response


def _selected_answer(consultation: Dict[str, Any]) -> Optional[str]:
    evaluation = consultation.get("evaluation") or {}
    selected = evaluation.get("selected") or {}
    answer = selected.get("answer")
    return str(answer).strip() if answer else None


def _external_stage(consultation: Dict[str, Any], message: str, cognitive: Dict[str, Any]) -> str:
    """Infer action-safety stage without claiming cognitive authority."""
    readiness = cognitive.get("action_readiness") or {}
    if readiness.get("eligible"):
        return "commitment_candidate"
    if consultation.get("used"):
        return cognitive.get("conversation_stage") or "conversation_or_diagnostic"
    return cognitive.get("conversation_stage") or "exploration"


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
    """Run cognitive scaffolding, then give the prepared context to external AI.

    The external AI is the reasoning authority. The deterministic layer only
    supplies context/memory/tool policy and prevents premature actions.
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

    cognitive = build_cognitive_state(
        message=message,
        company_context=context,
        memory=memory_dict,
        history=history,
    )

    # Keep the external rector first. Cognitive state is scaffolding, not a
    # substitute for model reasoning.
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
                "cognitive_state": cognitive,
            },
            conversation_id=memory_dict.get("conversation_id"),
        )
    except Exception as exc:
        print("[AI-FIRST CONSULTATION WARNING]", type(exc).__name__)
        consultation = {"used": False, "reason": "consultation_error"}

    answer = _selected_answer(consultation)
    stage = _external_stage(consultation, message, cognitive)

    if answer and stage != "commitment_candidate":
        response_check = evaluate_response(answer, cognitive)
        if response_check.get("accepted"):
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
                    "architecture": "ai_first_v31_cognitive_archetypes",
                    "cognitive_authority": "external_ai",
                    "bitey_role": "context_memory_tools_evaluation_learning",
                    "conversation_stage": stage,
                    "action_engine": "deferred",
                    "cognitive_state": cognitive,
                    "response_evaluation": response_check,
                    "ai_consultation": consultation,
                },
            }
        # A generic/catalog answer is not accepted when a concrete need exists.
        # Do not fall through to the legacy ticket engine.
        return {
            "action": "conversation",
            "create_ticket": False,
            "requires_quote": False,
            "ticket_type": None,
            "response": "Entiendo lo que necesitas. Para orientarte correctamente dentro de los servicios de esta empresa, dime qué resultado quieres conseguir y te hago la pregunta más útil para avanzar.",
            "workflow": None,
            "service": None,
            "service_id": None,
            "reasoning": {},
            "metadata": {
                "architecture": "ai_first_v31_cognitive_archetypes",
                "cognitive_authority": "external_ai",
                "bitey_role": "context_memory_tools_evaluation_learning",
                "conversation_stage": stage,
                "action_engine": "deferred",
                "cognitive_state": cognitive,
                "response_evaluation": response_check,
                "fallback": "contextual_safe_conversation",
            },
        }

    # Explicitly mature commitment can proceed to the action engine. The
    # action engine executes; it is not the cognitive authority.
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
            "architecture": "ai_first_v31_cognitive_archetypes",
            "cognitive_authority": "external_ai" if consultation.get("used") else "fallback",
            "bitey_role": "context_memory_tools_evaluation_learning",
            "conversation_stage": stage,
            "cognitive_state": cognitive,
            "ai_consultation": consultation,
        })
    return result
