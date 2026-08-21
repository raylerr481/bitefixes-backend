"""Bitey AI-first decision gateway.

External AI is the cognitive and conversational authority. Bitey is a second
plane: it supplies company context, memory, governed tools, persistence,
evaluation and action safety. It must not replace a valid external-AI answer
with a deterministic catalog/template response.
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
    if answer:
        return str(answer).strip()
    suggestions = consultation.get("suggestions") or []
    if suggestions:
        answer = suggestions[0].get("answer")
        if answer:
            return str(answer).strip()
    return None


def _external_stage(consultation: Dict[str, Any], cognitive: Dict[str, Any]) -> str:
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
    """Prepare the environment, let the external rector reason, then evaluate.

    Critical rule: evaluation is second-plane feedback. A deterministic
    evaluator may score/flag the answer, but it does not replace a valid
    external-AI answer with a generic catalog or canned response. The legacy
    action engine is reserved for mature, explicit commitments.
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
    stage = _external_stage(consultation, cognitive)

    # SECOND PLANE: evaluate and persist quality, but never replace the
    # external rector's conversational answer with a canned Bitey response.
    if answer:
        response_check = evaluate_response(answer, cognitive)
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
                "architecture": "external-rector-primary-v32",
                "cognitive_authority": "external_ai",
                "bitey_role": "second_plane_context_memory_tools_evaluation_learning",
                "conversation_stage": stage,
                "action_engine": "deferred" if stage != "commitment_candidate" else "commitment_guarded",
                "cognitive_state": cognitive,
                "response_evaluation": response_check,
                "ai_consultation": consultation,
            },
        }

    # If no external AI is available, do not silently pretend Bitey reasoned.
    # Return a transparent, contextual fallback without creating a ticket.
    if not (consultation.get("used") and answer):
        return {
            "action": "conversation",
            "create_ticket": False,
            "requires_quote": False,
            "ticket_type": None,
            "response": "Estoy preparando una respuesta dentro del contexto de esta empresa. Cuéntame qué resultado necesitas conseguir y continuaré desde ahí.",
            "workflow": None,
            "service": None,
            "service_id": None,
            "reasoning": {},
            "metadata": {
                "architecture": "external-rector-primary-v32",
                "cognitive_authority": "external_ai_unavailable",
                "bitey_role": "second_plane_context_memory_tools_evaluation_learning",
                "conversation_stage": stage,
                "action_engine": "deferred",
                "cognitive_state": cognitive,
                "ai_consultation": consultation,
            },
        }

    # Explicit mature commitment: the legacy engine may execute the action,
    # but only after the external rector has reasoned and the action gate says
    # the conversation is mature. The engine is an execution plane, not a
    # cognitive authority.
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
            "architecture": "external-rector-primary-v32",
            "cognitive_authority": "external_ai",
            "bitey_role": "second_plane_context_memory_tools_evaluation_learning",
            "conversation_stage": stage,
            "cognitive_state": cognitive,
            "ai_consultation": consultation,
        })
    return result
