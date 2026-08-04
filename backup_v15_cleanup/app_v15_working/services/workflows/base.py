"""
Workflow Base Utilities

Shared utilities for BiteFixes workflow engine.

Responsibilities:

- Standardize workflow responses.
- Handle workflow errors.
- Manage workflow actions.
- Extract knowledge information.
- Create or reuse support tickets.

Architecture:

Bitey
  |
  v
Workflow Service
  |
  v
Workflow Modules
  |
  v
Base Utilities
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.ticket_service import (
    create_ticket,
    get_open_ticket,
)


# =====================================================
# RESPONSE BUILDERS
# =====================================================


def build_response(
    response: str,
    intent: Optional[str] = None,
    ticket: Optional[Dict[str, Any]] = None,
    service_id: Optional[int] = None,
    actions: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Creates a standardized successful workflow response.
    """

    return {
        "success": True,
        "response": response,
        "ticket": ticket,
        "ticket_id": (
            ticket.get("id")
            if ticket
            else None
        ),
        "service_id": service_id,
        "intent": intent,
        "actions": actions or [],
        "metadata": metadata or {},
    }


def build_error(
    message: str,
    error: Optional[str] = None,
    actions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Creates a standardized workflow error response.
    """

    return {
        "success": False,
        "response": message,
        "error": error,
        "ticket": None,
        "ticket_id": None,
        "service_id": None,
        "intent": None,
        "actions": actions or [],
        "metadata": {},
    }


# =====================================================
# ACTION MANAGEMENT
# =====================================================


def add_action(
    actions: List[str],
    action: str,
) -> List[str]:
    """
    Adds an action avoiding duplicates.
    """

    if action not in actions:
        actions.append(action)

    return actions


# =====================================================
# KNOWLEDGE HELPERS
# =====================================================


def extract_knowledge(
    knowledge: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Extracts normalized information from knowledge results.
    """

    if not knowledge:
        return {
            "response": None,
            "service_id": None,
            "intent": None,
            "requires_ticket": False,
        }

    return {

        "response": knowledge.get(
            "answer"
        ),

        "service_id": knowledge.get(
            "service_id"
        ),

        "intent": knowledge.get(
            "intent"
        ),

        "requires_ticket": knowledge.get(
            "requires_ticket",
            False
        ),
    }


# =====================================================
# TICKET MANAGEMENT
# =====================================================


def get_or_create_ticket(
    company_id: int,
    customer_id: int,
    title: str,
    description: str,
    service_id: Optional[int],
    intent: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    Returns an existing open ticket or creates a new one.
    """

    try:

        ticket = get_open_ticket(
            customer_id,
            service_id
        )

        if ticket:
            return ticket


        return create_ticket(
            company_id,
            customer_id,
            title,
            description,
            service_id,
            intent,
        )


    except Exception as exc:

        print(
            "[WORKFLOW TICKET ERROR]",
            exc
        )

        return None


# =====================================================
# METADATA
# =====================================================


def merge_metadata(
    base: Optional[Dict[str, Any]],
    extra: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Merges workflow metadata.
    """

    result = {}

    if base:
        result.update(base)

    if extra:
        result.update(extra)

    return result