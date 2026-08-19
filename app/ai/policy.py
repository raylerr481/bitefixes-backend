"""Central safety and usage policy for Bitey AI orchestration."""
import os
import time
from threading import Lock
from typing import Any

ALLOWED_TASKS = {
    "general_reasoning", "semantic_interpretation", "language_detection",
    "information_extraction", "technical_diagnosis", "response_generation",
}
FORBIDDEN_ACTIONS = {
    "create_ticket", "update_customer", "delete_customer", "change_workflow",
    "execute_tool", "send_message", "change_price",
}
_lock = Lock()
_window_started = time.monotonic()
_calls = 0

def sanitize_context(context: dict[str, Any] | None) -> dict[str, Any]:
    if not context:
        return {}
    return {k: v for k, v in context.items() if k not in FORBIDDEN_ACTIONS}

def task_allowed(task: str) -> bool:
    return task in ALLOWED_TASKS

def allow_call() -> bool:
    """Process-local rate guard; production-wide quotas belong at the provider/gateway."""
    global _window_started, _calls
    limit = max(0, int(os.getenv("AI_MAX_CALLS_PER_MINUTE", "20")))
    if limit == 0:
        return False
    now = time.monotonic()
    with _lock:
        if now - _window_started >= 60:
            _window_started, _calls = now, 0
        if _calls >= limit:
            return False
        _calls += 1
        return True

def max_message_chars() -> int:
    return max(1000, int(os.getenv("AI_MAX_INPUT_CHARS", "6000")))
