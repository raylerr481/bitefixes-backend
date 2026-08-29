"""Bitey problem identity and continuity classifier.

A customer may have multiple simultaneous or historical problems. Only a
continuation/reopen of the same problem should reuse its active incident.
"""
from typing import Any, Dict, Optional
import re
import unicodedata


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", _norm(text)))


def _device_key(message: str) -> Optional[str]:
    text = _norm(message)
    patterns = [
        r"\b(redmi\s+note\s+\d+[a-z0-9]*)\b",
        r"\b(iphone\s*\d+[a-z0-9\s-]*)\b",
        r"\b(galaxy\s+[a-z0-9\s-]+)\b",
        r"\b(laptop|notebook|computador|pc|celular|telefone|tablet)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    return None


def classify_problem(message: str, current_intent: Optional[str] = None, active_intent: Optional[str] = None, active_problem: Optional[str] = None, active_device: Optional[str] = None) -> Dict[str, Any]:
    """Classify the message relative to the customer's active problem."""
    text = _norm(message)
    tokens = _tokens(message)
    current = _norm(current_intent)
    active = _norm(active_intent)
    device = _device_key(message)
    active_device_norm = _norm(active_device)
    reopen_markers = ("volvio", "regreso", "volveu", "reaparecio", "otra vez", "again", "de novo")

    if active_intent and current and current != active:
        state = "NEW_PROBLEM"
    elif active_device_norm and device and device != active_device_norm:
        state = "NEW_PROBLEM"
    elif active_intent and not current:
        state = "CONTINUATION" if active_problem else "NEEDS_CLARIFICATION"
    elif active_intent and current == active:
        state = "REOPENED_PROBLEM" if any(marker in text for marker in reopen_markers) else "CONTINUATION"
    else:
        state = "NEW_PROBLEM"

    if state == "NEW_PROBLEM" and active_problem and current == active:
        if len(tokens & _tokens(active_problem)) >= 2:
            state = "RELATED_PROBLEM"

    return {
        "state": state,
        "is_new": state == "NEW_PROBLEM",
        "is_continuation": state == "CONTINUATION",
        "is_reopened": state == "REOPENED_PROBLEM",
        "is_related": state == "RELATED_PROBLEM",
        "device": device,
        "current_intent": current_intent,
        "active_intent": active_intent,
    }
