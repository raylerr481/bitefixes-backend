"""Generic context resolver: separates a user's goal from a diagnostic symptom."""
from __future__ import annotations
import re
from typing import Any

_REQUEST_PATTERNS = (
    r"\bquiero\s+(?:instalar|crear|configurar|comprar|contratar|montar|hacer|adquirir|poner|implementar|desarrollar)\b",
    r"\b(?:deseo|necesito|busco|me gustaría|me gustaria)\s+(?:instalar|crear|configurar|comprar|contratar|montar|hacer|adquirir|poner|implementar|desarrollar)\b",
    r"\b(?:quiero|deseo|necesito|busco)\s+(?:una|un|el|la|las|los)\s+.+",
    r"\bcomo\s+(?:puedo|podría|podria)\s+(?:instalar|crear|configurar|comprar|contratar|montar|hacer)\b",
)
_SYMPTOM_MARKERS = ("no funciona", "no enciende", "no inicia", "no arranca", "está lento", "esta lento", "se congela", "se bloquea", "no muestra", "no conecta", "se desconecta", "no carga", "no graba", "roto", "rota", "dañado", "danado", "error", "problema", "falla", "falló", "fallo")

def _has_request_intent(text: str) -> bool:
    value = text.lower().strip()
    return any(re.search(pattern, value, flags=re.IGNORECASE) for pattern in _REQUEST_PATTERNS)

def _has_symptom(text: str) -> bool:
    value = text.lower().strip()
    return any(marker in value for marker in _SYMPTOM_MARKERS)

def resolve_context(state: dict[str, Any], current_message: str, history: list[dict[str, Any]]) -> dict[str, Any]:
    """Suppress diagnostic inference when the current turn is clearly a request."""
    text = str(current_message or "").strip()
    result = dict(state)
    if _has_request_intent(text) and not _has_symptom(text):
        result["active_problem"] = None
        result["active_category"] = None
        result["state"] = "GOAL_REQUEST"
        result["is_follow_up"] = bool(history)
        result["customer_goal"] = result.get("customer_goal") or "REQUEST_SERVICE"
        result["hypotheses"] = []
        result["confidence"] = max(float(result.get("confidence") or 0.0), 0.80)
        result["confirmed_facts"] = [f for f in result.get("confirmed_facts", []) if f.get("type") != "problem"]
    return result
