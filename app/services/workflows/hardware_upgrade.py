"""
=====================================================
BiteFixes Hardware Upgrade Workflow V16
=====================================================

Workflow:
    Hardware Upgrade

Responsibilities:
    • SSD upgrades
    • RAM upgrades
    • Performance optimization
    • Workflow response generation

This module NEVER:
    • Creates tickets
    • Saves messages
    • Creates notifications
    • Accesses the database

Those responsibilities belong to Bitey Core.

=====================================================
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.workflows.base import (
    build_response,
    build_error,
    extract_knowledge,
)

# =====================================================
# CONSTANTS
# =====================================================

WORKFLOW_NAME = "hardware_upgrade"

DEFAULT_RESPONSE = (
    "Podemos mejorar el rendimiento del notebook "
    "instalando un SSD y ampliando la memoria RAM."
)

DEFAULT_ACTIONS = [
    "hardware_upgrade",
    "technical_support",
]

# =====================================================
# WORKFLOW
# =====================================================

def execute(
    *,
    company_id: int,
    customer_id: int,
    message: str,
    knowledge: Optional[Dict[str, Any]] = None,
    service: Optional[Dict[str, Any]] = None,
    intent: Optional[str] = None,
    language: str = "es",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Executes the Hardware Upgrade workflow.

    Parameters
    ----------
    company_id
    customer_id
    message
    knowledge
    service
    intent
    language
    metadata

    Returns
    -------
    Standard workflow response.
    """

    try:

        info = extract_knowledge(knowledge)

        response = (
            info.get("response")
            or DEFAULT_RESPONSE
        )

        service_id = (
            info.get("service_id")
            or (
                service.get("id")
                if service
                else None
            )
        )

        workflow_metadata = {
            "workflow": WORKFLOW_NAME,
            "language": language,
            **(metadata or {}),
        }

        return build_response(
            response=response,
            intent=intent,
            service_id=service_id,
            actions=DEFAULT_ACTIONS.copy(),
            metadata=workflow_metadata,
        )

    except Exception as exc:

        print(
            f"[{WORKFLOW_NAME.upper()} ERROR]",
            repr(exc),
        )

        return build_error(
            message="No fue posible ejecutar el workflow.",
            error=str(exc),
        )