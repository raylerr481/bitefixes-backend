"""Bitey cognitive archetypes.

These are deterministic scaffolding around the external AI rector. They do not
replace model reasoning; they build the state, preserve conversational
references, select the next useful question, and gate actions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List
import re


@dataclass
class CognitiveState:
    company_context: Dict[str, Any]
    active_topic: str | None
    active_object: str | None
    user_need: Dict[str, Any]
    conversation_stage: str
    candidate_services: List[Dict[str, Any]]
    missing_information: List[str]
    tool_need: Dict[str, Any]
    action_readiness: Dict[str, Any]
    directives: List[str]


def _text(message: str) -> str:
    return " ".join(str(message or "").strip().lower().split())


def _last_text(history: Iterable[Dict[str, Any]]) -> str:
    for row in reversed(list(history or [])):
        value = row.get("message") or row.get("response") or row.get("content")
        if value:
            return str(value)
    return ""


def resolve_reference(message: str, history: Iterable[Dict[str, Any]], memory: Dict[str, Any]) -> str | None:
    text = _text(message)
    explicit = {
        "telefono": "phone", "teléfono": "phone", "celular": "phone", "móvil": "phone", "movil": "phone",
        "laptop": "computer", "computadora": "computer", "ordenador": "computer", "notebook": "computer",
        "camara": "cctv", "cámara": "cctv", "camaras": "cctv", "cámaras": "cctv",
        "red": "network", "wifi": "network", "ia": "ai_business",
    }
    for token, obj in explicit.items():
        if re.search(rf"\b{re.escape(token)}\b", text):
            return obj
    prior = memory.get("active_object")
    if prior:
        return str(prior)
    previous = _text(_last_text(history))
    for token, obj in explicit.items():
        if re.search(rf"\b{re.escape(token)}\b", previous):
            return obj
    return None


def infer_need(message: str, active_object: str | None, memory: Dict[str, Any]) -> Dict[str, Any]:
    text = _text(message)
    need = {"raw": message, "normalized": None, "object": active_object, "confidence": 0.0}
    if any(x in text for x in ("contratar una ia", "contratar ia", "una ia para mi empresa", "ia para mi empresa")):
        need.update(normalized="improve_business_service_with_ai", confidence=0.92)
    elif active_object == "phone" and any(x in text for x in ("quebrad", "roto", "rota", "pantalla", "no enciende", "no carga")):
        need.update(normalized="mobile_repair", confidence=0.90)
    elif active_object == "computer" and any(x in text for x in ("lenta", "lento", "no enciende", "pantalla", "repar")):
        need.update(normalized="computer_repair", confidence=0.88)
    elif active_object == "cctv" and any(x in text for x in ("instalar", "camaras", "cámaras", "seguridad")):
        need.update(normalized="cctv_installation", confidence=0.90)
    elif text:
        need.update(normalized="explore_user_need", confidence=0.45)
    return need


def choose_missing_information(need: Dict[str, Any], company_context: Dict[str, Any], memory: Dict[str, Any]) -> List[str]:
    normalized = need.get("normalized")
    if normalized == "improve_business_service_with_ai":
        return ["business_type", "improvement_area"]
    if normalized == "mobile_repair":
        return ["device_model"] if not memory.get("device_model") else []
    if normalized == "cctv_installation":
        return ["installation_location", "camera_quantity_or_coverage"]
    return []


def stage_for(need: Dict[str, Any], memory: Dict[str, Any]) -> str:
    if memory.get("conversation_stage") in {"diagnostic", "proposal", "commitment_candidate"}:
        return memory["conversation_stage"]
    if need.get("normalized") in {"improve_business_service_with_ai", "mobile_repair", "computer_repair", "cctv_installation"}:
        return "diagnostic" if need.get("confidence", 0) >= 0.8 else "exploration"
    return "exploration"


def build_cognitive_state(*, message: str, company_context: Dict[str, Any] | None, memory: Dict[str, Any] | None, history: Iterable[Dict[str, Any]] | None) -> Dict[str, Any]:
    company_context = company_context or {}
    memory = memory if isinstance(memory, dict) else {}
    history = list(history or memory.get("history", []) or [])
    active_object = resolve_reference(message, history, memory)
    need = infer_need(message, active_object, memory)
    missing = choose_missing_information(need, company_context, memory)
    stage = stage_for(need, memory)
    explicit_commitment = bool(re.search(r"\b(quiero contratar|deseo contratar|quiero comprar|quero contratar|quero comprar)\b", _text(message)))
    readiness = {
        "eligible": explicit_commitment and not missing,
        "need_confirmed": need.get("confidence", 0) >= 0.8,
        "scope_known": not bool(missing),
        "user_commitment": explicit_commitment,
        "reason": "explicit_commitment_and_scope" if explicit_commitment and not missing else "conversation_not_mature_for_action",
    }
    tool_need = {"web_search": any(x in _text(message) for x in ("buscar", "busca", "web", "internet", "cep", "dirección", "endereco"))}
    directives = [
        "Respond from the active company profile and conversation context.",
        "Treat external AI as the cognitive authority for reasoning.",
        "Do not return the service catalog unless the user asks for it or it is necessary.",
        "Ask the smallest useful question when information is missing.",
        "Do not create a ticket from intent detection alone.",
        "Use tools when current or external evidence is required; never invent facts.",
    ]
    state = CognitiveState(company_context, memory.get("active_topic"), active_object, need, stage, [], missing, tool_need, readiness, directives)
    return asdict(state)


def evaluate_response(response: str, state: Dict[str, Any]) -> Dict[str, Any]:
    text = _text(response)
    catalog_terms = ("puedo ayudarte con", "soporte técnico, celulares", "computadoras, redes, cámaras")
    is_catalog = sum(term in text for term in catalog_terms) >= 1
    need = state.get("user_need", {})
    contextual = bool(text) and (not is_catalog or need.get("normalized") in {None, "explore_user_need"})
    return {"accepted": contextual, "contextual": contextual, "catalog_response": is_catalog, "reason": "contextual" if contextual else "catalog_without_user_request"}
