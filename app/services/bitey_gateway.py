"""Bitey Cloud Gateway - shared context, memory and response flow for every channel."""
from __future__ import annotations
import os
from typing import Any

from app.services.decision_engine_v29 import decision_engine as ai_first_decision
from app.services.customer_service import get_or_create_customer
from app.services.conversation_service import get_or_create_conversation, update_conversation_context
from app.services.message_service import save_customer_message, save_bitey_message, get_conversation_history
from app.services.website_diagnostic_service import extract_urls, fetch_website_context
from app.services.problem_state_service import build_problem_state
from app.cognitive.idempotency_guard import IdempotencyGuard
from app.cognitive.identity_scope import IdentityScope

SUPPORTED_CHANNELS = {"website", "whatsapp", "messenger", "telegram", "email", "sms", "phone", "app", "private", "api"}
_INTERNAL_KEYS = {"intent", "confidence", "raw_intent_score", "knowledge", "knowledge_found", "memory", "ai_consultation", "comparative_evaluation", "response_source", "decision", "gateway_debug"}
_IDEMPOTENCY = IdempotencyGuard()


def normalize_channel(channel: str | None) -> str:
    value = str(channel or "website").strip().lower()
    return value if value in SUPPORTED_CHANNELS else "api"


def _public_result(result: dict[str, Any]) -> dict[str, Any]:
    if os.getenv("BITEY_PUBLIC_DEBUG", "false").lower() == "true": return result
    public = {k: v for k, v in result.items() if k not in _INTERNAL_KEYS}
    public.pop("gateway", None); public.pop("metadata", None)
    public["public_contract"] = "bitey-chat-v1"
    return public


def _db_conversation_id(value: str | None) -> int | None:
    try:
        text = str(value or "").strip()
        return int(text) if text.isdigit() else None
    except (TypeError, ValueError): return None


def _channel_identity(channel: str, phone: str, conversation_id: str | None) -> tuple[str, str]:
    supplied, external = str(phone or "").strip(), str(conversation_id or "").strip()
    if channel == "website":
        stable = external or supplied
        return (f"web:{stable}", stable) if stable and stable.lower() not in {"web", "unknown", "anonymous"} else ("web:anonymous", "")
    if channel in {"telegram", "messenger", "instagram"}:
        stable = supplied or external
        return (f"{channel}:{stable}" if stable else f"{channel}:anonymous", stable)
    if channel in {"whatsapp", "phone"}:
        stable = supplied or external
        return stable, stable
    stable = supplied or external
    return stable or f"{channel}:anonymous", stable


def _website_context(history: list[dict[str, Any]], message: str, state: dict[str, Any]) -> dict[str, Any] | None:
    urls = extract_urls(message)
    for row in reversed(history[-12:]): urls.extend(extract_urls(str(row.get("message_content") or row.get("ai_response") or "")))
    unique_urls = list(dict.fromkeys(urls))
    if not unique_urls: return None
    target = unique_urls[-1]
    requested = bool(state.get("website_diagnostic_requested"))
    if not requested and not extract_urls(message): return {"reference_url": target, "diagnostic_requested": False}
    try:
        context = fetch_website_context(target); context["diagnostic_requested"] = True; return context
    except Exception as exc: return {"reference_url": target, "diagnostic_requested": True, "fetch_error": type(exc).__name__}


def _try_external_ai(*, company_id: int, message: str, channel: str, phone: str, email: str, customer_name: str, last_name: str, conversation_id: str | None, external_message_id: str | None, language: str, preferred_contact_channel: str | None) -> dict[str, Any]:
    identity_phone, external_identity = _channel_identity(channel, phone, conversation_id)
    customer = get_or_create_customer(company_id=company_id, phone=identity_phone, email=str(email or "").strip(), name=" ".join(x for x in (customer_name, last_name) if x).strip() or "Customer", channel=channel, external_id=external_identity)
    customer_id = customer.get("id") if isinstance(customer, dict) else None
    if not customer_id: return {"action":"conversation","create_ticket":False,"response":"No fue posible establecer la identidad de la conversación en este momento."}
    db_cid = _db_conversation_id(conversation_id)
    conversation = get_or_create_conversation(customer_id=customer_id, channel=channel, conversation_id=db_cid)
    cid = conversation.get("id") if isinstance(conversation, dict) else None
    history = get_conversation_history(company_id=company_id, customer_id=customer_id, conversation_id=cid) if cid else []
    state = build_problem_state(history, message)
    website_context = _website_context(history, message, state)
    memory = {"conversation_id":cid,"external_conversation_id":conversation_id,"history":history,"recent_turns":state.get("recent_turns",[]),"confirmed_facts":state.get("confirmed_facts",[]),"last_service":next((row.get("service_id") for row in reversed(history[-16:]) if row.get("service_id") is not None),None),"active_topic":state.get("active_category"),"active_object":state.get("active_object"),"active_model":state.get("active_model"),"active_problem":state.get("active_problem"),"active_action":None,"active_location":state.get("active_location"),"active_url":None,"website_diagnostic_requested":state.get("website_diagnostic_requested",False),"stage":"diagnosis" if state.get("active_problem") else "exploration","is_follow_up":state.get("is_follow_up",False),"problem_state":state,"current_message":message}
    business_context = {"channel":channel,"conversation":{"state":state.get("state"),"active_problem":state.get("active_problem"),"active_category":state.get("active_category"),"active_object":state.get("active_object"),"active_model":state.get("active_model"),"active_location":state.get("active_location"),"symptoms":state.get("symptoms",[]),"hypotheses":state.get("hypotheses",[]),"customer_goal":state.get("customer_goal"),"confidence":state.get("confidence"),"confirmed_facts":state.get("confirmed_facts",[])}}
    if website_context: business_context["website_context"] = website_context; business_context["website_diagnostic"] = bool(website_context.get("diagnostic_requested"))
    result = ai_first_decision(company_id=company_id, customer=customer, message=message, intent={}, knowledge=None, memory=memory, language=language, business_context=business_context)
    if not isinstance(result,dict): return {"action":"conversation","create_ticket":False,"response":"No fue posible completar la consulta en este momento."}
    response=str(result.get("response") or "").strip(); result_service_id=result.get("service_id") or memory.get("last_service"); result_intent=result.get("intent")
    if cid:
        save_customer_message(company_id=company_id,customer_id=customer_id,conversation_id=cid,message=message,channel=channel,service_id=result_service_id)
        if response: save_bitey_message(company_id=company_id,customer_id=customer_id,conversation_id=cid,response=response,channel=channel,service_id=result_service_id)
        update_conversation_context(cid,intent=result_intent,response=response,service_id=result_service_id,language=language)
    result["conversation_id"]=cid; result["external_conversation_id"]=conversation_id; result["customer_id"]=customer_id
    if preferred_contact_channel: result["preferred_contact_channel"]=preferred_contact_channel
    return result


def handle_message(*, company_id: int, message: str, channel: str = "website", phone: str = "", email: str = "", customer_name: str = "Customer", last_name: str = "", conversation_id: str | None = None, external_message_id: str | None = None, language_preference: str = "auto", preferred_contact_channel: str | None = None) -> dict[str, Any]:
    normalized_channel = normalize_channel(channel)
    if not str(message or "").strip(): return _public_result({"success":False,"response":"Escribe un mensaje para continuar."})

    identity = IdentityScope(company_id=company_id, channel=normalized_channel, conversation_id=str(conversation_id or "anonymous"), user_id=phone or email or None, external_message_id=external_message_id)
    if external_message_id:
        key = identity.message_key(message)
        existing = _IDEMPOTENCY.get(key)
        if existing is not None:
            return existing

    # WhatsApp uses the canonical Bitey Core flow for real webhook traffic.
    if normalized_channel == "whatsapp":
        from app.core.bitey import process_message
        result = process_message(company_id=company_id,message=str(message).strip(),phone=phone,email=email,customer_name=customer_name,last_name=last_name,channel="whatsapp",conversation_id=conversation_id,language_preference=language_preference)
    else:
        language = language_preference if language_preference not in (None,"","auto") else "es"
        result = _try_external_ai(company_id=company_id,message=str(message).strip(),channel=normalized_channel,phone=phone,email=email,customer_name=customer_name,last_name=last_name,conversation_id=conversation_id,external_message_id=external_message_id,language=language,preferred_contact_channel=preferred_contact_channel)
    public_result = _public_result(result)
    if external_message_id:
        _IDEMPOTENCY.mark(key, public_result)
    return public_result
