"""Central safety policy for Bitey AI orchestration."""
from typing import Any

ALLOWED_TASKS = {
    "general_reasoning",
    "semantic_interpretation",
    "language_detection",
    "information_extraction",
    "technical_diagnosis",
    "response_generation",
}

FORBIDDEN_ACTIONS = {
    "create_ticket",
    "update_customer",
    "delete_customer",
    "change_workflow",
    "execute_tool",
    "send_message",
    "change_price",
}


def sanitize_context(context: dict[str, Any] | None) -> dict[str, Any]:
    """Strip action authority from context sent to external models."""
    if not context:
        return {}
    blocked = set(FORBIDDEN_ACTIONS)
    return {k: v for k, v in context.items() if k not in blocked}


def task_allowed(task: str) -> bool:
    return task in ALLOWED_TASKS
