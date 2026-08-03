"""
Bitey Decision Engine V10

Central business decision layer.

Flow
-----
Intent
    ↓
Resolve Service (Supabase)
    ↓
Sales / Workflow Routing
    ↓
Structured Decision
"""

from typing import Any

from app.services.service_resolver import resolve_service
from app.services.sales_engine import generate_sales_response
from app.services.workflows.workflow_service import execute_workflow


SALES_INTENTS = {
    "ai_assistant",
    "sales",
    "quote",
    "purchase",
}

SUPPORT_INTENTS = {
    "computer_repair",
    "hardware_upgrade",
    "windows_installation",
    "network_configuration",
    "cctv_installation",
    "mobile_repair",
    "software_problem",
}


def decision_engine(
    company_id: int,
    customer: dict,
    message: str,
    intent: dict,
    knowledge=None,
    memory=None,
):
    """
    Main Bitey decision engine.
    """

    try:

        intent_name = None
        confidence = 0

        if isinstance(intent, dict):
            intent_name = intent.get("intent")
            confidence = intent.get("confidence", 0)

        # --------------------------------------------------
        # Resolve service from Supabase
        # --------------------------------------------------

        service = resolve_service(
            company_id,
            intent_name,
        )

        service_id = None

        if service:
            service_id = service.get("id")

        print(
            "[DECISION ENGINE]",
            {
                "intent": intent_name,
                "confidence": confidence,
                "service_id": service_id,
            },
        )

        # --------------------------------------------------
        # SALES
        # --------------------------------------------------

        if intent_name in SALES_INTENTS:

            response = generate_sales_response(
                intent_name,
                customer.get("full_name", "Cliente"),
                memory,
            )

            return {
                "action": "sales",
                "create_ticket": True,
                "ticket_type": "sales",
                "response": response,
                "workflow": None,
                "ticket": None,
                "service": service,
                "service_id": service_id,
                "metadata": {
                    "intent": intent_name,
                    "confidence": confidence,
                },
            }

        # --------------------------------------------------
        # TECHNICAL
        # --------------------------------------------------

        if intent_name in SUPPORT_INTENTS:

            workflow = execute_workflow(
                intent_name,
                company_id,
                message,
                knowledge,
                intent,
            )

            return {
                "action": "workflow",
                "create_ticket": True,
                "ticket_type": "technical_support",
                "response": workflow.get(
                    "response",
                    "Solicitud recibida.",
                ),
                "workflow": intent_name,
                "ticket": workflow.get("ticket"),
                "service": service,
                "service_id": service_id,
                "metadata": {
                    "intent": intent_name,
                    "confidence": confidence,
                },
            }

        # --------------------------------------------------
        # DEFAULT
        # --------------------------------------------------

        return {
            "action": "support",
            "create_ticket": True,
            "ticket_type": "support",
            "response": "Gracias por contactar BiteFixes. Vamos a revisar tu solicitud.",
            "workflow": "default",
            "ticket": None,
            "service": service,
            "service_id": service_id,
            "metadata": {
                "intent": intent_name,
                "confidence": confidence,
            },
        }

    except Exception as error:

        print("[DECISION ENGINE ERROR]", repr(error))

        return {
            "action": "error",
            "create_ticket": False,
            "response": "Error procesando solicitud.",
            "service": None,
            "service_id": None,
            "ticket": None,
        }