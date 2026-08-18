"""
BiteFixes Decision Engine V16

Flow:
Intent -> Business Context -> Business Reasoning -> Service -> Workflow

Business reasoning guides the response when semantic data is available, while
legacy workflows remain the execution fallback.
"""

from typing import Any, Dict, Optional

from app.services.company_service import get_company_context
from app.services.business_reasoning_service import resolve_business_reasoning
from app.services.service_resolver import resolve_service
from app.services.workflows.workflow_service import execute_workflow
from app.services.sales_engine import generate_sales_response

SALES_INTENTS = {"ai_assistant", "sales", "quote", "purchase"}
SUPPORT_INTENTS = {
    "computer_repair", "hardware_upgrade", "windows_installation",
    "mobile_repair", "cctv_installation", "camera_installation",
    "network_configuration", "software_problem", "remote_support",
}
QUOTE_INTENTS = {
    "ai_assistant", "sales", "quote", "purchase", "cctv_installation",
    "camera_installation", "network_configuration", "hardware_upgrade",
}


def _reasoning_response(reasoning: Dict[str, Any], language: Optional[str]) -> Optional[str]:
    """Build a deterministic clarification response from semantic requirements."""
    step = reasoning.get("next_step")
    if not step:
        return None

    if step.get("type") == "collect_requirements":
        requirements = step.get("requirements", [])
        names = [r.get("name") for r in requirements if r.get("name")]
        if not names:
            return None
        if language == "pt-BR":
            return "Para orientá-lo melhor, preciso de: " + ", ".join(names) + "."
        if language == "en":
            return "To guide you better, I need: " + ", ".join(names) + "."
        return "Para orientarte mejor, necesito: " + ", ".join(names) + "."

    if step.get("type") == "clarify_need":
        need = (step.get("needs") or [{}])[0]
        return need.get("description") or need.get("name")

    if step.get("type") == "present_solution":
        solution = (step.get("solutions") or [{}])[0]
        return solution.get("description") or solution.get("name")

    return None


def make_decision(
    company_id: int,
    customer: Dict,
    message: str,
    intent: Dict,
    knowledge=None,
    memory=None,
    language=None,
    channel="unknown",
    business_context: Optional[Dict[str, Any]] = None,
):
    intent_name = intent.get("intent") if intent else None
    confidence = intent.get("confidence", 0) if intent else 0

    if business_context is None:
        try:
            business_context = get_company_context(company_id)
        except Exception as error:
            print("[BUSINESS CONTEXT WARNING]", error)
            business_context = None

    reasoning = resolve_business_reasoning(company_id, intent_name)
    service = resolve_service(company_id, intent_name, business_context=business_context)
    service_id = service.get("id") if service else None
    requires_quote = intent_name in QUOTE_INTENTS

    metadata = {
        "intent": intent_name,
        "confidence": confidence,
        "requires_quote": requires_quote,
        "business_context_loaded": bool(business_context),
        "ai_scope_loaded": bool(business_context and business_context.get("ai_scope")),
        "business_reasoning_found": reasoning.get("reasoning_found", False),
        "next_step": (reasoning.get("next_step") or {}).get("type"),
        "needs_count": len(reasoning.get("needs", [])),
        "requirements_count": len(reasoning.get("requirements", [])),
        "solutions_count": len(reasoning.get("solutions", [])),
        "actions_count": len(reasoning.get("actions", [])),
    }

    semantic_response = _reasoning_response(reasoning, language)

    if intent_name in SALES_INTENTS:
        response = semantic_response or generate_sales_response(
            intent_name, customer.get("full_name", "Cliente"), memory
        )
        return {
            "action": "sales", "create_ticket": True,
            "requires_quote": requires_quote, "ticket_type": "sales",
            "response": response, "service": service, "service_id": service_id,
            "workflow": None, "reasoning": reasoning, "metadata": metadata,
        }

    if intent_name in SUPPORT_INTENTS:
        workflow = execute_workflow(
            intent=intent_name, company_id=company_id,
            customer_id=customer.get("id"), service_id=service_id,
            message=message, knowledge=knowledge, language=language,
            business_context=business_context, intent_data=intent,
        )
        return {
            "action": "workflow", "create_ticket": True,
            "requires_quote": requires_quote, "ticket_type": "technical_support",
            "response": semantic_response or workflow.get("response", "Solicitud recibida."),
            "workflow": intent_name, "ticket": workflow.get("ticket"),
            "service": service, "service_id": service_id,
            "reasoning": reasoning, "metadata": metadata,
        }

    return {
        "action": "support", "create_ticket": True,
        "requires_quote": requires_quote, "ticket_type": "support",
        "response": semantic_response or "Gracias por contactar BiteFixes.",
        "workflow": None, "service": service, "service_id": service_id,
        "reasoning": reasoning, "metadata": metadata,
    }


def decision_engine(company_id, customer, message, intent, knowledge=None, memory=None, language=None, business_context=None):
    return make_decision(
        company_id, customer, message, intent, knowledge, memory, language,
        business_context=business_context,
    )
