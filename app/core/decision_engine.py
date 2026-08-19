"""Bitey Decision Engine V19."""

from typing import Any, Dict, Optional

from app.services.company_service import get_company_context
from app.services.service_resolver import resolve_service
from app.services.workflows.workflow_service import execute_workflow
from app.services.sales_engine import generate_sales_response
from app.services.semantic_match_service import match_semantic_context
from app.services.ai_provider import ai_provider

SALES_INTENTS = {
    "ai_assistant", "quote", "purchase", "sales", "cctv_installation", "camera_installation"
}

SUPPORT_INTENTS = {
    "computer_repair", "hardware_upgrade", "upgrade_hardware", "windows_installation",
    "mobile_repair", "network_configuration", "software_problem", "remote_support"
}


def _load_business_context(company_id: int, supplied_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if supplied_context is not None:
        return supplied_context
    try:
        return get_company_context(company_id)
    except Exception as error:
        print("[DECISION CONTEXT ERROR]", error)
        return {}


def _scope_allows_intent(context: Dict[str, Any], intent_name: Optional[str]) -> bool:
    if not intent_name:
        return True
    policy = (context.get("ai_scope") or {}).get("policy") or {}
    blocked = policy.get("blocked_intents")
    allowed = policy.get("allowed_intents")
    if isinstance(blocked, list) and intent_name in blocked:
        return False
    if isinstance(allowed, list) and allowed:
        return intent_name in allowed
    return True


def _ai_fallback(message: str, customer: Dict, context: Dict[str, Any], language: Optional[str]) -> Optional[str]:
    """Use OpenAI only for conversational wording; never authorize actions."""
    return ai_provider.respond(
        system=(
            "You are Bitey, the conversational AI for a business. "
            "Answer helpfully and briefly in the requested language. "
            "Do not invent prices, services, policies, customer data, or actions. "
            "Do not claim that a ticket, quote, payment, or external action was completed. "
            "Bitey Core controls all business actions."
        ),
        user=message,
        context={
            "customer_name": customer.get("name"),
            "language": language,
            "company_context": context,
        },
    )


def make_decision(
    company_id: int,
    customer: Dict,
    message: str,
    intent: Dict,
    knowledge=None,
    memory=None,
    channel="unknown",
    business_context: Optional[Dict[str, Any]] = None,
    language: Optional[str] = None,
):
    """Produce the next business action without performing persistence."""
    try:
        customer = customer or {}
        memory = memory or {}
        intent = intent or {}
        context = _load_business_context(company_id, business_context)
        semantic_context = match_semantic_context(
            message, company_id=company_id, language=context.get("language") or language
        )
        intent_name = intent.get("intent")
        confidence = intent.get("confidence", 0)
        scope_allowed = _scope_allows_intent(context, intent_name)
        service = resolve_service(company_id, intent_name, context)
        service_id = service.get("id") if service else None

        metadata = {
            "intent": intent_name, "confidence": confidence, "channel": channel,
            "company_id": company_id, "business_context_loaded": bool(context),
            "scope_allowed": scope_allowed,
            "ai_scope_id": (context.get("ai_scope") or {}).get("id"),
            "plan_id": ((context.get("subscription") or {}).get("plan") or {}).get("id"),
            "domain_count": len(context.get("domains") or []),
            "capability_count": len(context.get("capabilities") or []),
            "semantic_confidence": semantic_context.get("confidence", 0.0),
            "semantic_matches": semantic_context.get("matches", [])[:5],
            "semantic_relations": semantic_context.get("relations", [])[:20],
        }

        if intent_name and not scope_allowed:
            return {"action": "scope_restricted", "create_ticket": False, "requires_quote": False,
                    "ticket_type": None, "response": "Esta solicitud no está habilitada para la configuración actual de Bitey.",
                    "service": service, "service_id": service_id, "semantic_context": semantic_context,
                    "business_context": context, "metadata": metadata}

        if knowledge and not intent_name:
            return {"action": "knowledge", "create_ticket": False, "ticket_type": None,
                    "response": knowledge, "service": service, "service_id": service_id,
                    "semantic_context": semantic_context, "business_context": context, "metadata": metadata}

        if intent_name in SALES_INTENTS:
            sales = generate_sales_response(intent_name, message, memory, knowledge)
            return {"action": "sales", "create_ticket": False, "requires_quote": True,
                    "ticket_type": "sales", "response": sales, "service": service,
                    "service_id": service_id, "semantic_context": semantic_context,
                    "business_context": context, "metadata": metadata}

        if intent_name in SUPPORT_INTENTS:
            workflow = execute_workflow(
                intent=intent_name, company_id=company_id, customer_id=customer.get("id"),
                message=message, knowledge=knowledge, customer=customer,
                language=language or context.get("language") or channel,
                business_context=context,
            ) or {}
            workflow_success = bool(workflow.get("success"))
            create_ticket = bool(workflow.get("create_ticket", False)) and workflow_success
            return {
                "action": "workflow" if workflow_success else "conversation",
                "create_ticket": create_ticket,
                "requires_quote": bool(workflow.get("requires_quote", False)),
                "ticket_type": "technical_support" if create_ticket else None,
                "response": workflow.get("response") or _ai_fallback(message, customer, context, language) or
                    "Puedo ayudarte a diagnosticarlo. Necesito algunos datos para continuar.",
                "workflow": intent_name, "workflow_success": workflow_success,
                "workflow_reason": workflow.get("reason"), "service": service, "service_id": service_id,
                "semantic_context": semantic_context, "business_context": context, "metadata": metadata,
            }

        response = _ai_fallback(message, customer, context, language)
        return {"action": "conversation", "create_ticket": False, "requires_quote": False,
                "ticket_type": None, "response": response, "service": service, "service_id": service_id,
                "semantic_context": semantic_context, "business_context": context, "metadata": metadata}

    except Exception as error:
        import traceback
        traceback.print_exc()
        return {"action": "error", "create_ticket": False, "response": "Error procesando solicitud.",
                "service": None, "service_id": None, "business_context": {}}


def decision_engine(company_id, customer, message, intent, knowledge=None, memory=None, channel="unknown", business_context=None, language=None):
    return make_decision(company_id, customer, message, intent, knowledge, memory, channel, business_context, language)
