"""Governed AI-council ticket lifecycle.

Exactly one external provider is delegated execution authority while Bitey is
still an apprentice. The delegation is narrow: the provider can only execute a
write after the council reaches an explicit consensus gate. Other providers
remain independent analysts/reviewers and cannot write business data.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable

from app.services.ticket_service import close_ticket, create_ticket


TICKET_EXECUTOR = "groq"
ANALYSTS = {"groq", "deepseek-free", "qwen-free"}
TERMINAL_STATES = {"resolved", "closed", "cancelled", "completed"}


class TicketGovernanceError(RuntimeError):
    """Raised when the AI council has not authorized a ticket lifecycle write."""


def _votes(results: Iterable[Dict[str, Any]], decision_key: str) -> list[str]:
    return [
        str(item.get("provider"))
        for item in results
        if item.get("provider") in ANALYSTS and item.get(decision_key) is True
    ]


def evaluate_ticket_creation(
    *,
    context: Dict[str, Any],
    provider_results: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """Decide whether the council has enough evidence to create a ticket.

    Creation requires: an identified user/customer, a concrete problem, no
    already-active ticket, and agreement from at least two council members.
    A single model can never trigger creation by itself.
    """
    results = list(provider_results)
    approvals = _votes(results, "recommend_create_ticket")
    missing = []
    if not context.get("customer_id"):
        missing.append("customer_id")
    if not context.get("problem"):
        missing.append("problem")
    if context.get("active_ticket"):
        missing.append("active_ticket_already_exists")

    approved = not missing and len(set(approvals)) >= 2
    return {
        "action": "create_ticket" if approved else "continue_conversation",
        "approved": approved,
        "executor": TICKET_EXECUTOR if approved else None,
        "approvals": sorted(set(approvals)),
        "missing": missing,
        "reason": "council_consensus" if approved else "insufficient_evidence_or_consensus",
    }


def evaluate_ticket_closure(
    *,
    context: Dict[str, Any],
    provider_results: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """Decide whether work is demonstrably finished before closing a ticket."""
    results = list(provider_results)
    approvals = _votes(results, "recommend_close_ticket")
    evidence = bool(context.get("resolution_evidence"))
    user_confirmed = bool(context.get("user_confirmed"))
    ticket_id = context.get("ticket_id")
    current_status = str(context.get("status") or "").lower()

    approved = (
        bool(ticket_id)
        and evidence
        and user_confirmed
        and current_status not in TERMINAL_STATES
        and len(set(approvals)) >= 2
    )
    return {
        "action": "close_ticket" if approved else "continue_work",
        "approved": approved,
        "executor": TICKET_EXECUTOR if approved else None,
        "approvals": sorted(set(approvals)),
        "reason": "resolution_verified_by_council" if approved else "resolution_not_proven",
    }


def execute_ticket_creation(*, decision: Dict[str, Any], ticket_data: Dict[str, Any]) -> Any:
    """Execute the only AI-authorized business write: Groq after council approval."""
    if decision.get("approved") is not True:
        raise TicketGovernanceError("ticket_creation_not_authorized")
    if decision.get("executor") != TICKET_EXECUTOR:
        raise TicketGovernanceError("invalid_ticket_executor")
    return create_ticket(**ticket_data)


def execute_ticket_closure(*, decision: Dict[str, Any], ticket_id: int, solution: str) -> Any:
    """Close a ticket only through the same delegated executor boundary."""
    if decision.get("approved") is not True:
        raise TicketGovernanceError("ticket_closure_not_authorized")
    if decision.get("executor") != TICKET_EXECUTOR:
        raise TicketGovernanceError("invalid_ticket_executor")
    return close_ticket(ticket_id, solution=solution)
