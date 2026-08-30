"""Single bridge between conversation context and Bitey's cognitive loop.

The bridge is domain-agnostic: services provide requirements; the bridge
tracks what is known, missing, conflicting, and what should happen next.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


def _mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def merge_context(*sources: Any) -> Dict[str, Any]:
    """Merge context without replacing established values with empty values."""
    result: Dict[str, Any] = {}
    for source in sources:
        source = _mapping(source)
        for key, value in source.items():
            if value is None or value == "" or value == [] or value == {}:
                continue
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = merge_context(result[key], value)
            else:
                result[key] = value
    return result


def resolve_active_problem(*, current: Dict[str, Any], memory: Dict[str, Any], identity: Dict[str, Any]) -> Dict[str, Any]:
    """Create the canonical active-problem context for the reasoning layer."""
    current = _mapping(current)
    memory = _mapping(memory)
    identity = _mapping(identity)
    problem = merge_context(
        memory.get("active_problem"),
        memory.get("problem"),
        current.get("active_problem"),
        current.get("problem"),
        identity,
    )
    if current.get("intent") and not problem.get("intent"):
        problem["intent"] = current["intent"]
    if current.get("service_id") and not problem.get("service_id"):
        problem["service_id"] = current["service_id"]
    return problem


def build_cognitive_context(
    *,
    message: str,
    current: Optional[Dict[str, Any]] = None,
    memory: Optional[Dict[str, Any]] = None,
    identity: Optional[Dict[str, Any]] = None,
    business: Optional[Dict[str, Any]] = None,
    knowledge: Optional[Iterable[Any]] = None,
    evidence: Optional[Iterable[Any]] = None,
) -> Dict[str, Any]:
    """Produce one canonical packet consumed by reasoning and decision layers."""
    current = _mapping(current)
    memory = _mapping(memory)
    identity = _mapping(identity)
    business = _mapping(business)
    problem = resolve_active_problem(current=current, memory=memory, identity=identity)

    known = merge_context(problem.get("known"), current.get("known"), current.get("entities"))
    missing = list(current.get("missing") or problem.get("missing") or [])
    contradictions = list(current.get("contradictions") or problem.get("contradictions") or [])
    asked = list(memory.get("questions_asked") or current.get("questions_asked") or [])

    return {
        "message": message,
        "goal": current.get("goal") or problem.get("goal"),
        "active_problem": problem,
        "known": known,
        "missing": missing,
        "contradictions": contradictions,
        "questions_asked": asked,
        "customer": current.get("customer") or memory.get("customer") or {},
        "business": business,
        "services": business.get("services") or [],
        "knowledge": list(knowledge or []),
        "evidence": list(evidence or []),
    }
