"""Generic semantic resolver: separates a user's goal from a diagnostic symptom.

This layer is deliberately domain-neutral. A service/object mentioned in a request
is not treated as a fault unless the conversation contains evidence of a symptom.
"""
from __future__ import annotations
import re
from typing import Any

_REQUEST_PATTERNS = (
    r"\bquiero\s+(?:instalar|crear|configurar|comprar|contratar|montar|hacer|adquirir|poner|implementar|desarrollar)\b",
    r"\b(?:deseo|necesito|busco|me gustaría|me gustaria)\s+(?:instalar|crear|configurar|comprar|contratar|montar|hacer|adquirir|poner|implementar|desarrollar)\b",
    r"\b(?:quiero|deseo|necesito|busco)\s+(?:una|un|el|la|las|los)\s+.+",
    r"\bcomo\s+(?:puedo|podría|podria)\s+(?:instalar|crear|configurar|comprar|contratar|montar|hacer)\b",
)
_SYMPTOM_MARKERS = (
    "no funciona", "no enciende", "no inicia", "no arranca", "está lento", "esta lento",
    "se congela", "se bloquea", "no muestra", "no conecta", "se desconecta", "no carga",
    "no graba", "roto", "rota", "dañado", "danado", "error", "problema", "falla", "falló", "fallo",
)

def _has_request_intent(text: str) -> bool:
    value = text.lower().strip()
    return any(re.search(pattern, value, flags=re.IGNORECASE) for pattern in _REQUEST_PATTERNS)

def _has_symptom(text: str) -> bool:
    value = text.lower().strip()
    return any(marker in value for marker in _SYMPTOM_MARKERS)

def _history_has_request(history: list[dict[str, Any]]) -> bool:
    for row in history:
        if str(row.get("sender_type") or "").lower() not in {"customer", "user"}:
            continue
        text = str(row.get("message_content") or "").strip()
        if text and _has_request_intent(text) and not _has_symptom(text):
            return True
    return False

def resolve_context(state: dict[str, Any], current_message: str, history: list[dict[str, Any]]) -> dict[str, Any]:
    """Resolve the current turn against the existing goal before allowing a fault.

    If a prior turn established a service/request goal and the current turn merely
    supplies non-symptomatic details, those details update the request instead of
    becoming a diagnostic problem. This is intentionally independent of service
    names (CCTV, Windows, notebook, phone, etc.).
    """
    text = str(current_message or "").strip()
    result = dict(state)
    current_request = _has_request_intent(text)
    current_symptom = _has_symptom(text)
    prior_request = _history_has_request(history)

    if current_request and not current_symptom:
        result["active_problem"] = None
        result["active_category"] = None
        result["state"] = "GOAL_REQUEST"
        result["is_follow_up"] = bool(history)
        result["customer_goal"] = result.get("customer_goal") or "REQUEST_SERVICE"
        result["active_goal"] = result.get("active_goal") or result["customer_goal"]
        result["hypotheses"] = []
        result["confidence"] = max(float(result.get("confidence") or 0.0), 0.80)
        result["confirmed_facts"] = [f for f in result.get("confirmed_facts", []) if f.get("type") != "problem"]
        return result

    # A detail/update after an established request belongs to that request unless
    # the user explicitly reports a symptom. This is the key continuity invariant.
    if prior_request and not current_symptom:
        result["active_problem"] = None
        result["active_category"] = None
        result["state"] = "ENTITY_UPDATE" if result.get("entity_only") else "CONTINUATION"
        result["is_follow_up"] = True
        result["customer_goal"] = result.get("customer_goal") or "REQUEST_SERVICE"
        result["active_goal"] = result.get("active_goal") or result["customer_goal"]
        result["hypotheses"] = []
        result["confidence"] = max(float(result.get("confidence") or 0.0), 0.80)
        result["confirmed_facts"] = [f for f in result.get("confirmed_facts", []) if f.get("type") != "problem"]

    return result
