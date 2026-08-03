"""
Hardware Upgrade Workflow

Handles hardware upgrade requests.

Examples:

- SSD upgrade
- RAM upgrade
- Performance improvement
- Hardware optimization


Architecture:

Bitey
 |
 v
Workflow Service
 |
 v
Hardware Upgrade Workflow
 |
 +--> Ticket Service
 |
 +--> Base Utilities
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.workflows.base import (
    build_response,
    build_error,
    add_action,
    extract_knowledge,
    get_or_create_ticket,
)


# =====================================================
# EXECUTE
# =====================================================


def execute(
    company_id: int,
    customer_id: int,
    message: str,
    knowledge: Optional[Dict[str, Any]] = None,
    intent: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute hardware upgrade workflow.
    """

    actions = []


    try:

        add_action(
            actions,
            "hardware_upgrade_started"
        )


        knowledge_data = extract_knowledge(
            knowledge
        )


        response = (
            knowledge_data.get("response")
            or
            "Podemos realizar upgrade de SSD "
            "e memória RAM para melhorar "
            "o desempenho do equipamento."
        )


        service_id = knowledge_data.get(
            "service_id"
        )


        workflow_intent = (
            knowledge_data.get("intent")
            or
            (
                intent.get("intent")
                if intent
                else "hardware_upgrade"
            )
        )


        ticket = None


        if knowledge_data.get(
            "requires_ticket",
            True
        ):

            ticket = get_or_create_ticket(

                company_id=company_id,

                customer_id=customer_id,

                title="Hardware Upgrade",

                description=message,

                service_id=service_id,

                intent=workflow_intent

            )


            if ticket:

                add_action(
                    actions,
                    "ticket_created_or_found"
                )


                response += (

                    "\n\nSeu atendimento foi registrado. "

                    f"Código do ticket: "
                    f"{ticket.get('codigo_ticket')}"

                )


        return build_response(

            response=response,

            intent=workflow_intent,

            ticket=ticket,

            service_id=service_id,

            actions=actions,

            metadata={

                "workflow":
                    "hardware_upgrade"

            }

        )


    except Exception as exc:


        print(
            "[HARDWARE WORKFLOW ERROR]",
            exc
        )


        return build_error(

            message=(
                "No fue posible procesar "
                "el upgrade de hardware."
            ),

            error=str(exc),

            actions=actions

        )