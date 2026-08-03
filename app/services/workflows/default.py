"""
Default Workflow

Fallback workflow for BiteFixes.

Responsibilities:

- Handle unknown intents.
- Return a standard response.
- Avoid unnecessary ticket creation.
- Provide workflow metadata.

Architecture:

Bitey
 |
 v
Workflow Service
 |
 v
Default Workflow
 |
 v
Base Utilities
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.workflows.base import (
    build_response,
    add_action,
)


# =====================================================
# EXECUTE DEFAULT WORKFLOW
# =====================================================


def execute(
    company_id: int,
    customer_id: int,
    message: str,
    knowledge: Optional[Dict[str, Any]] = None,
    intent: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute fallback workflow.

    Used when no specialized workflow
    matches the customer request.
    """

    actions = []


    add_action(
        actions,
        "default_workflow_executed"
    )


    detected_intent = None


    if intent:

        detected_intent = intent.get(
            "intent"
        )


    response = (
        "Obrigado pela mensagem. "
        "Recebi sua solicitação e "
        "vou direcionar para análise."
    )


    return build_response(

        response=response,

        intent=detected_intent,

        ticket=None,

        service_id=None,

        actions=actions,

        metadata={

            "workflow": "default",

            "company_id": company_id,

            "customer_id": customer_id,

            "message": message

        }

    )