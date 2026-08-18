"""
BiteFixes Decision Engine V13

Central business reasoning layer.

The decision engine consumes the normalized company business context so
service resolution and workflow routing can use the tenant's configured
domains, capabilities, services and AI scope without confusing commercial
subscription limits with operational business context.
"""

from typing import Any, Dict, Optional

from app.services.service_resolver import resolve_service
from app.services.workflows.workflow_service import execute_workflow
from app.services.sales_engine import generate_sales_response


SALES_INTENTS = {"ai_assistant", "sales", "quote", "purchase"}

SUPPORT_INTENTS = {
    "computer_repair",
    "hardware_upgrade",
    "windows_installation",
    "mobile_repair",
    "cctv_installation",
    "camera_installation",
    "network_configuration",
    "software_problem",
}

QUOTE_INTENTS = {
    "ai_assistant",
    "sales",
    "quote",
    "purchase",
    "cctv_installation",
    "camera_installation",
    "network_configuration",
    "hardware_upgrade",
}


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

    # Operational resolution is driven by company context. Subscription data
    # remains available in business_context but does not block service access.
    service = resolve_service(
        company_id,
        intent_name,
        business_context=business_context,
    )
    service_id = service.get("id") if service else None
    requires_quote = intent_name in QUOTE_INTENTS

    metadata = {
        "intent": intent_name,
        "confidence": confidence,
        "requires_quote": requires_quote,
        "business_context_loaded": bool(business_context),
        "ai_scope_loaded": bool(
            business_context and business_context.get("ai_scope")
        ),
    }

    print(
        "[DECISION ENGINE]",
        {
            "intent": intent_name,
            "confidence": confidence,
            "service_id": service_id,
            "requires_quote": requires_quote,
            "business_context_loaded": bool(business_context),
        },
    )

    if intent_name in SALES_INTENTS:
        response = generate_sales_response(
            intent_name,
            customer.get("full_name", "Cliente"),
            memory,
        )
        return {
            "action": "sales",
            "create_ticket": True,
            "requires_quote": requires_quote,
            "ticket_type": "sales",
            "response": response,
            "service": service,
            "service_id": service_id,
            "workflow": None,
            "metadata": metadata,
        }

    if intent_name in SUPPORT_INTENTS:
        workflow = execute_workflow(
            intent=intent_name,
            company_id=company_id,
            customer_id=customer.get("id"),
            service_id=service_id,
            message=message,
            knowledge=knowledge,
            language=language,
            business_context=business_context,
            intent_data=intent,
        )
        return {
            "action": "workflow",
            "create_ticket": True,
            "requires_quote": requires_quote,
            "ticket_type": "technical_support",
            "response": workflow.get("response", "Solicitud recibida."),
            "workflow": intent_name,
            "ticket": workflow.get("ticket"),
            "service": service,
            "service_id": service_id,
            "metadata": metadata,
        }

    return {
        "action": "support",
        "create_ticket": True,
        "requires_quote": requires_quote,
        "ticket_type": "support",
        "response": "Gracias por contactar BiteFixes.",
        "workflow": None,
        "service": service,
        "service_id": service_id,
        "metadata": metadata,
    }


def decision_engine(
    company_id,
    customer,
    message,
    intent,
    knowledge=None,
    memory=None,
    language=None,
    business_context=None,
):
    return make_decision(
        company_id,
        customer,
        message,
        intent,
        knowledge,
        memory,
        language,
        business_context=business_context,
    )
