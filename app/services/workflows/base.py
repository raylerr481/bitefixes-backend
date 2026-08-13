"""
=====================================================
BiteFixes Workflow Base Utilities V17
=====================================================

Shared utilities for the BiteFixes Workflow Engine.

Responsibilities
----------------
- Standard workflow responses
- Error handling
- Workflow actions
- Knowledge normalization
- Ticket management
- Metadata management
- CRM preparation

Architecture

Bitey Core
    |
    v
Decision Engine
    |
    v
Workflow Router
    |
    v
Workflow Module
    |
    v
Workflow Base Utilities
=====================================================
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.ticket_service import (
    process_ticket,
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
    Build a standard successful workflow response.
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


# =====================================================
# ERROR RESPONSE
# =====================================================

def build_error(
    message: str,
    error: Optional[str] = None,
    actions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build a standard workflow error response.
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
# ACTIONS
# =====================================================

def add_action(
    actions: List[str],
    action: str,
) -> List[str]:
    """
    Add an action without creating duplicates.
    """

    if action not in actions:
        actions.append(action)

    return actions


# =====================================================
# KNOWLEDGE
# =====================================================

def extract_knowledge(
    knowledge: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Normalize knowledge-base information.

    Returns a predictable structure even when
    no knowledge was found.
    """

    if not knowledge:
        return {
            "response": None,
            "service_id": None,
            "intent": None,
            "requires_ticket": False,
        }

    return {
        "response": (
            knowledge.get("answer")
            or knowledge.get("response")
            or knowledge.get("resposta")
        ),

        "service_id":
            knowledge.get("service_id"),

        "intent":
            knowledge.get("intent"),

        "requires_ticket":
            knowledge.get(
                "requires_ticket",
                False,
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
    language: str = "es",
    channel: str = "website",
    ticket_type: str = "technical_support",
) -> Optional[Dict[str, Any]]:
    """
    Return an existing compatible active ticket
    or create a new one.

    IMPORTANT
    ---------
    Ticket reuse is delegated to ticket_service.process_ticket().

    process_ticket() uses find_open_ticket(), which validates:

        customer_id
        company_id
        intent
        service_id
        active status

    This prevents the old workflow-base implementation
    from reusing a ticket merely because the customer
    and service matched.
    """

    try:

        ticket = process_ticket(

            company_id=company_id,

            customer_id=customer_id,

            service_id=service_id,

            intent=intent,

            description=description,

            title=title,

            language=language,

            channel=channel,

            ticket_type=ticket_type,
        )

        if ticket:

            print(
                "[WORKFLOW TICKET]",
                "Ticket obtained:",
                ticket.get("ticket_code")
                or ticket.get("codigo_ticket")
                or ticket.get("id"),
            )

        else:

            print(
                "[WORKFLOW TICKET]",
                "No ticket returned",
            )

        return ticket

    except Exception as exc:

        print(
            "[WORKFLOW TICKET ERROR]",
            exc,
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
    Merge two metadata dictionaries.

    Values from 'extra' override values from 'base'.
    """

    result: Dict[str, Any] = {}

    if base:
        result.update(base)

    if extra:
        result.update(extra)

    return result


# =====================================================
# WORKFLOW RESULT NORMALIZATION
# =====================================================

def normalize_workflow_result(
    result: Any,
    service_id: Optional[int] = None,
    intent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Normalize the result returned by a workflow.

    Guarantees that the workflow result is always
    represented as a dictionary.
    """

    if isinstance(result, dict):

        normalized = dict(result)

    else:

        normalized = {
            "success": True,
            "response": str(result),
        }

    normalized.setdefault(
        "success",
        True,
    )

    normalized.setdefault(
        "response",
        "",
    )

    normalized.setdefault(
        "ticket",
        None,
    )

    normalized.setdefault(
        "ticket_id",
        (
            normalized["ticket"].get("id")
            if isinstance(
                normalized.get("ticket"),
                dict,
            )
            else None
        ),
    )

    normalized.setdefault(
        "service_id",
        service_id,
    )

    normalized.setdefault(
        "intent",
        intent,
    )

    normalized.setdefault(
        "actions",
        [],
    )

    normalized.setdefault(
        "metadata",
        {},
    )

    return normalized