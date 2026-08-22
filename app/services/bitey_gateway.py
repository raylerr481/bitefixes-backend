"""Bitey Cloud Gateway - shared context, memory and response flow for every channel."""
from __future__ import annotations
import os
import re
from typing import Any

from app.services.decision_engine_v29 import decision_engine as ai_first_decision
from app.services.customer_service import get_or_create_customer
from app.services.conversation_service import get_or_create_conversation
from app.services.message_service import save_customer_message, save_bitey_message, get_conversation_history

SUPPORTED_CHANNELS = {"website", "whatsapp", "messenger", "telegram", "email", "sms", "phone", "app", "private", "api"}
_INTERNAL_KEYS = {"intent", "confidence", "raw_intent_score", "knowledge", "knowledge_found", "memory", "ai_consultation", "comparative_evaluation", "response_source", "decision", "gateway_debug"}


def normalize_channel(channel: str | None) -> str:
    value = str(channel or "website").strip().lower()
    return value if value in SUPPORTED_CHANNELS else "api"


def _public_result(result: dict[str, Any]) -> dict[str, Any]:
    if os.getenv("BITEY_PUBLIC_DEBUG", "false").lower() == "true":
        return result
    public = {k: v for k, v in result.items() if k not in _INTERNAL_KEYS}
    public.pop("gateway", None)
    public.pop("metadata", None)
    public["public_contract"] = "bitey-chat-v1"
    return public


def _conversation_key(channel: str, conversation_id: str | None) -> str:
    return f"{channel}:{conversation_id}" if conversation_id else f"{channel}:anonymous"


def _db_conversation_id(value: str | None) -> int | None:
    try:
        if value in (None, ""):
            return None
        text = str(value).strip()
        if text.isdigit():
            return int(text)
    except (TypeError, ValueError):
        pass
    return None


def _derive_conversation_state(history: list[dict[str, Any]], current_message: str) -> dict[str, Any]:
    """Build a compact, relevance-oriented state from the existing conversation.

    This is context reconstruction, not answer generation. It deliberately avoids
    hard-coding a service catalog so the same mechanism works for BiteFixes and
    future companies/channels. External AI remains responsible for reasoning.
    """
    recent = history[-12:]
    user_rows = [row for row in recent if str(row.get("sender_type") or "").lower() in {"customer", "user"}]
    texts = [str(row.get("message_content") or row.get("ai_response") or "").strip() for row in recent]
    user_texts = [str(row.get("message_content") or "").strip() for row in user_rows]
    full_text = " ".join(texts).lower()
    current = str(current_message or "").strip().lower()
    combined = f"{full_text} {current}"

    phone_terms = r"\b(telefono|teléfono|móvil|movil|celular|smartphone|mobile|phone|cell)\b"
    computer_terms = r"\b(notebook|laptop|computadora|ordenador|pc|computer)\b"
    tablet_terms = r"\b(tablet|ipad)\b"
    screen_terms = r"\b(pantalla|screen|display|lcd|touch)\b"
    broken_terms = r"\b(roto|rota|quebrado|quebrada|rompió|rompio|dañado|danado|broken|cracked|damaged)\b"
    repair_terms = r"\b(reparar|reparación|reparacion|arreglar|arreglo|repair|fix|sustituir|sustituya|reemplazar|cambiar|cambio)\b"
    replace_terms = r"\b(sustituir|sustituya|reemplazar|cambiar|cambio|replace|replacement)\b"

    if re.search(phone_terms, combined):
        active_object = "teléfono móvil"
    elif re.search(computer_terms, combined):
        active_object = "computadora/notebook"
    elif re.search(tablet_terms, combined):
        active_object = "tablet"
    else:
        active_object = None

    # Preserve the most recently established device/model. This is deliberately
    # generic enough for the existing catalog and prevents follow-ups such as
    # "quiero sustituirla" from losing the previously supplied model.
    model_patterns = [
        r"\b(redmi\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
        r"\b(xiaomi\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
        r"\b(iphone\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
        r"\b(samsung\s+(?:galaxy\s+)?[a-z0-9][a-z0-9 ._-]{0,24})\b",
        r"\b(galaxy\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
        r"\b(moto(?:rola)?\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
    ]
    active_model = None
    for pattern in model_patterns:
        matches = re.findall(pattern, combined, flags=re.IGNORECASE)
        if matches:
            candidate = str(matches[-1]).strip(" .,_-\t\n")
            candidate = re.sub(r"\s+", " ", candidate)
            candidate = re.split(r"\b(?:y|pero|solo|porque|que|con|esta|está|tiene|tengo|deseo|quiero)\b", candidate, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            if 2 <= len(candidate) <= 32:
                active_model = candidate
                break

    if active_object == "teléfono móvil" and re.search(screen_terms, combined) and re.search(broken_terms, combined):
        active_problem = "pantalla rota/quebrada"
    elif re.search(broken_terms, combined) and active_object:
        active_problem = "daño físico"
    else:
        active_problem = None

    if active_object == "teléfono móvil" and (re.search(repair_terms, combined) or active_problem):
        active_topic = "reparación de teléfono móvil"
    elif active_object == "computadora/notebook" and re.search(repair_terms, combined):
        active_topic = "reparación de computadora"
    else:
        active_topic = None

    active_action = "sustitución/reemplazo" if re.search(replace_terms, combined) else ("reparación" if re.search(repair_terms, combined) else None)

    # Keep an explicit location when the user has supplied one. This is useful
    # across channels without tying the gateway to one city or business.
    location_patterns = [
        r"\b(?:en|desde|estoy en|ubicado en|ubicada en)\s+([a-záéíóúñü][a-záéíóúñü0-9 .,'-]{2,80})",
        r"\b(esteio(?:\s+centro)?(?:\s*,?\s*porto\s+alegre)?(?:\s*,?\s*rio\s+grande\s+do\s+sul)?)\b",
    ]
    active_location = None
    for row_text in reversed(user_texts + [str(current_message or "")]):
        for pattern in location_patterns:
            match = re.search(pattern, row_text, flags=re.IGNORECASE)
            if match:
                candidate = (match.group(1) if match.lastindex else match.group(0)).strip(" .,_-\t\n")
                candidate = re.sub(r"\s+", " ", candidate)
                if 3 <= len(candidate) <= 90:
                    active_location = candidate
                    break
        if active_location:
            break

    active_service = next((row.get("service_id") for row in reversed(recent) if row.get("service_id") is not None), None)
    short_followup = len(current.split()) <= 18 and bool(active_object or active_model or active_topic or active_service or active_location)

    # Confirmed user facts are compacted into a small list. These are facts
    # inferred from what the user already said, not instructions to the model.
    confirmed_facts = []
    for label, value in (
        ("objeto", active_object),
        ("modelo", active_model),
        ("problema", active_problem),
        ("acción", active_action),
        ("ubicación", active_location),
        ("servicio_id", active_service),
    ):
        if value not in (None, ""):
            confirmed_facts.append(f"{label}: {value}")

    return {
        "active_object": active_object,
        "active_model": active_model,
        "active_topic": active_topic,
        "active_problem": active_problem,
        "active_action": active_action,
        "active_location": active_location,
        "active_service": active_service,
        "confirmed_facts": confirmed_facts,
        "stage": "diagnosis" if active_topic or active_problem else "exploration",
        "is_follow_up": short_followup,
        "recent_turns": recent,
    }


def _try_external_ai(*, company_id: int, message: str, channel: str, phone: str, email: str,
                     customer_name: str, last_name: str, conversation_id: str | None, language: str,
                     preferred_contact_channel: str | None) -> dict[str, Any]:
    identity_phone = str(phone or "").strip() or _conversation_key(channel, conversation_id)
    customer = get_or_create_customer(company_id=company_id, phone=identity_phone, email=str(email or "").strip(), name=" ".join(x for x in (customer_name, last_name) if x).strip() or "Customer")
    customer_id = customer.get("id") if isinstance(customer, dict) else None
    if not customer_id:
        return {"action": "conversation", "create_ticket": False, "response": "No fue posible establecer la identidad de la conversación en este momento."}

    db_cid = _db_conversation_id(conversation_id)
    conversation = get_or_create_conversation(customer_id=customer_id, channel=channel, conversation_id=db_cid)
    cid = conversation.get("id") if isinstance(conversation, dict) else None
    history = get_conversation_history(company_id=company_id, customer_id=customer_id, conversation_id=cid) if cid else []
    state = _derive_conversation_state(history, message)

    memory = {
        "conversation_id": cid,
        "external_conversation_id": conversation_id,
        "history": history,
        "recent_turns": state.get("recent_turns", []),
        "confirmed_facts": state.get("confirmed_facts", []),
        "last_service": state.get("active_service"),
        "active_topic": state.get("active_topic"),
        "active_object": state.get("active_object"),
        "active_model": state.get("active_model"),
        "active_problem": state.get("active_problem"),
        "active_action": state.get("active_action"),
        "active_location": state.get("active_location"),
        "stage": state.get("stage", "exploration"),
        "is_follow_up": state.get("is_follow_up", False),
        "current_message": message,
    }

    result = ai_first_decision(company_id=company_id, customer=customer, message=message, intent={}, knowledge=None, memory=memory, language=language, business_context={"channel": channel})
    if not isinstance(result, dict):
        return {"action": "conversation", "create_ticket": False, "response": "No fue posible completar la consulta en este momento."}

    response = str(result.get("response") or "").strip()
    result_service_id = result.get("service_id") or state.get("active_service")
    if cid:
        save_customer_message(company_id=company_id, customer_id=customer_id, conversation_id=cid, message=message, channel=channel, service_id=result_service_id)
        if response:
            save_bitey_message(company_id=company_id, customer_id=customer_id, conversation_id=cid, response=response, channel=channel, service_id=result_service_id)

    result["conversation_id"] = cid
    result["external_conversation_id"] = conversation_id
    result["customer_id"] = customer_id
    if preferred_contact_channel:
        result["preferred_contact_channel"] = preferred_contact_channel
    return result


def handle_message(*, company_id: int, message: str, channel: str = "website", phone: str = "", email: str = "", customer_name: str = "Customer", last_name: str = "", conversation_id: str | None = None, language_preference: str = "auto", preferred_contact_channel: str | None = None) -> dict[str, Any]:
    normalized_channel = normalize_channel(channel)
    language = language_preference if language_preference not in (None, "", "auto") else "es"
    if not str(message or "").strip():
        return _public_result({"success": False, "response": "Escribe un mensaje para continuar."})
    result = _try_external_ai(company_id=company_id, message=str(message).strip(), channel=normalized_channel, phone=phone, email=email, customer_name=customer_name, last_name=last_name, conversation_id=conversation_id, language=language, preferred_contact_channel=preferred_contact_channel)
    return _public_result(result)
