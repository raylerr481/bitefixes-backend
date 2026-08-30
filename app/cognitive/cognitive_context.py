"""Canonical cognitive context envelope used across Bitey's reasoning pipeline."""
from __future__ import annotations

from typing import Any, Dict, List


def merge_non_empty(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """Merge facts without letting absent/empty follow-up values erase context."""
    result = dict(base or {})
    for key, value in (incoming or {}).items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_non_empty(result[key], value)
        else:
            result[key] = value
    return result


def dedupe(items: List[Any]) -> List[Any]:
    out: List[Any] = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def reconcile(
    previous: Dict[str, Any] | None,
    current: Dict[str, Any] | None,
    *,
    identity_state: str | None = None,
    is_new_problem: bool = False,
) -> Dict[str, Any]:
    """Reconcile one turn with the active cognitive state.

    The message is treated as an update to a persistent goal/problem, not as
    an independent intent classification. A NEW_PROBLEM transition is the
    only operation allowed to discard the previous active problem/service.
    """
    previous = dict(previous or {})
    current = dict(current or {})

    if is_new_problem or identity_state == "NEW_PROBLEM":
        base = {"known_facts": {}, "questions_already_asked": [], "evidence": [], "hypotheses": [], "contradictions": []}
    else:
        base = previous

    state = merge_non_empty(base, current)
    state["known_facts"] = merge_non_empty(previous.get("known_facts", {}), current.get("known_facts", {})) if not is_new_problem else dict(current.get("known_facts", {}))
    for field in ("questions_already_asked", "evidence", "hypotheses", "contradictions"):
        state[field] = dedupe(list(base.get(field, [])) + list(current.get(field, [])))
    if identity_state:
        state["identity_state"] = identity_state
    state["is_new_problem"] = bool(is_new_problem)
    return state


def next_best_action(state: Dict[str, Any]) -> str:
    """Generic action selection; service-specific requirements remain data-driven."""
    if state.get("contradictions"):
        return "resolve_contradiction"
    if state.get("missing_facts"):
        return "ask_clarification"
    if state.get("active_goal") or state.get("active_problem") or state.get("active_service"):
        return "advance_service"
    return "understand_request"
