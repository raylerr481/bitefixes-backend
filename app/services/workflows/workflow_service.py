"""
=====================================================
BiteFixes Workflow Router V16
=====================================================

Central workflow dispatcher.

Flow

Customer
    │
    ▼
Intent Detection
    │
    ▼
Workflow Router
    │
    ▼
Workflow Module
    │
    ▼
Workflow Result

The router NEVER:

- creates tickets
- saves messages
- creates notifications

Those responsibilities belong to Bitey Core.

=====================================================
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from app.services.workflows import (
    ai_assistant,
    camera_installation,
    computer_repair,
    default,
    hardware_upgrade,
    mobile_repair,
    network_support,
    windows_installation,
)


# =====================================================
# WORKFLOW REGISTRY
# =====================================================

WORKFLOW_MAP: Dict[str, Callable] = {

    "computer_repair":
        computer_repair.execute,

    "hardware_upgrade":
        hardware_upgrade.execute,

    "mobile_repair":
        mobile_repair.execute,

    "windows_installation":
        windows_installation.execute,

    "network_configuration":
        network_support.execute,

    "network_support":
        network_support.execute,

    "cctv_installation":
        camera_installation.execute,

    "camera_installation":
        camera_installation.execute,

    "ai_assistant":
        ai_assistant.execute,

}


# =====================================================
# ROUTER
# =====================================================

def execute_workflow(
    *,
    intent: Optional[str],
    company_id: int,
    customer_id: int,
    message: str,
    knowledge: Optional[Dict[str, Any]] = None,
    service: Optional[Dict[str, Any]] = None,
    language: str = "es",
    metadata: Optional[Dict[str, Any]] = None,
):

    workflow = WORKFLOW_MAP.get(
        intent,
        default.execute
    )

    try:

        print(
            "[WORKFLOW ROUTER]",
            {
                "intent": intent,
                "module": workflow.__module__
            }
        )

        return workflow(

            company_id=company_id,

            customer_id=customer_id,

            message=message,

            knowledge=knowledge,

            service=service,

            intent=intent,

            language=language,

            metadata=metadata or {}

        )

    except Exception as error:

        print(
            "[WORKFLOW ERROR]",
            repr(error)
        )

        return {

            "success": False,

            "workflow": intent,

            "response":
                "Workflow execution failed.",

            "error":
                str(error)

        }