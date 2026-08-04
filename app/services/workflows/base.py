"""
=====================================================
BiteFixes Workflow Base Utilities V16
=====================================================

Shared utilities for the BiteFixes Workflow Engine.

Responsibilities
----------------
✓ Standard workflow responses
✓ Error handling
✓ Workflow actions
✓ Knowledge extraction
✓ Ticket management
✓ CRM preparation

Architecture

Bitey Core
    │
    ▼
Workflow Router
    │
    ▼
Workflow Module
    │
    ▼
Workflow Base Utilities

=====================================================
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
    Standard successful workflow response.
    """

    return {
        "success": True,
        "response": response,
        "ticket": ticket,
        "ticket_id": ticket.get("id") if ticket else None,
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
    Standard workflow error response.
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
    Adds an action avoiding duplicates.
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
    Normalizes knowledge base information.
    """

    if not knowledge:
        return {
            "response": None,
            "service_id": None,
            "intent": None,
            "requires_ticket": False,
        }

    return {
        "response": knowledge.get("answer"),
        "service_id": knowledge.get("service_id"),
        "intent": knowledge.get("intent"),
        "requires_ticket": knowledge.get("requires_ticket", False),
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
    Returns an existing open ticket.
    Creates a new ticket if none exists.
    """

    try:

        ticket = get_open_ticket(
            customer_id=customer_id,
            service_id=service_id,
        )

        if ticket:
            return ticket

        return create_ticket(
            customer_id=customer_id,
            service_id=service_id,
            description=description,
            title=title,
            intent=intent,
            company_id=company_id,
            channel=channel,
            language=language,
            ticket_type=ticket_type,
        )

    except Exception as exc:

        print("[WORKFLOW TICKET ERROR]", exc)

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

    result: Dict[str, Any] = {}

    if base:
        result.update(base)

    if extra:
        result.update(extra)

    return result