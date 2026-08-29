"""Bitey Self-Service Guide Engine.

Turns research-backed troubleshooting into an interactive, stateful guide.
It never claims a diagnosis without evidence and escalates when risk or
complexity makes professional intervention preferable.
"""
from __future__ import annotations
from typing import Any, Dict

RISK_WORDS = {"password", "bank", "payment", "crypto", "ransomware", "stolen", "data loss", "fire", "smoke", "battery swelling"}


def assess_risk(problem: Dict[str, Any], message: str) -> str:
    text = str(message or "").lower()
    if any(word in text for word in RISK_WORDS):
        return "high"
    if problem.get("category") in {"malware", "power"}:
        return "medium"
    return "low"


def choose_mode(*, problem: Dict[str, Any], message: str, customer_choice: str | None = None) -> str:
    choice = str(customer_choice or "").strip().lower()
    if choice in {"self", "self_service", "guide", "do_it_myself", "yo_mismo"}:
        return "SELF_SERVICE_GUIDE"
    if choice in {"bitefixes", "professional", "remote", "workshop"}:
        return "BITEFIXES_SERVICE"
    return "OFFER_OPTIONS"


def build_guide(*, problem: Dict[str, Any], research: Dict[str, Any] | None = None, step: int = 1, customer_choice: str | None = None) -> Dict[str, Any]:
    research = research or {}
    risk = assess_risk(problem, problem.get("problem_summary", ""))
    mode = choose_mode(problem=problem, message=problem.get("problem_summary", ""), customer_choice=customer_choice)
    sources = research.get("evidence_sources") or research.get("sources") or []
    if mode != "SELF_SERVICE_GUIDE":
        return {"mode": mode, "risk_level": risk, "requires_confirmation": True, "sources": sources}
    return {
        "mode": "SELF_SERVICE_GUIDE",
        "risk_level": risk,
        "step": max(1, int(step)),
        "interactive": True,
        "one_step_at_a_time": True,
        "verify_after_each_step": True,
        "stop_if_unexpected": True,
        "escalate_if_risk_high": risk == "high",
        "sources": sources,
    }


def record_step_result(*, guide: Dict[str, Any], success: bool, observation: str = "") -> Dict[str, Any]:
    next_step = int(guide.get("step", 1)) + 1 if success else int(guide.get("step", 1))
    return {**guide, "last_step_success": bool(success), "last_observation": observation[:1000], "next_step": next_step}
