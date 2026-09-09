"""Bitey Cloud Gateway - shared context, memory and response flow for every channel."""
from __future__ import annotations
import os
import re
from typing import Any
from app.services.decision_engine_v29 import decision_engine as ai_first_decision
from app.services.customer_service import get_or_create_customer
from app.services.conversation_service import get_or_create_conversation, update_conversation_context
from app.services.message_service import save_customer_message, save_bitey_message, get_conversation_history
from app.services.website_diagnostic_service import extract_urls, fetch_website_context
from app.services.problem_state_service import build_problem_state
from app.services.contextual_resolution import resolve_context

SUPPORTED_CHANNELS = {"website", "whatsapp", "messenger", "telegram", "email", "sms", "phone", "app", "private", "api"}
_INTERNAL_KEYS = {"intent", "confidence", "raw_intent_score", "knowledge", "knowledge_found", "memory", "ai_consultation", "comparative_evaluation", "response_source", "decision", "gateway_debug"}
_OPTION_RE = re.compile(r"^\s*(\d{1,2})\s*[.)\-:]\s*(.+?)\s*$")
_RESET_GREETING = r"(?:hola|hello|hi|hey|oi|ola|olá|buenas|buenos dias|buenos días|buenas tardes|buenas noches)"
_RESET_ACTION = r"(?:prueba(?:\s+de)?\s+(?:conexi[oó]n(?:\s+multicanal)?|telegram|whatsapp)|prueba\s+multicanal|nuevo problema|otra consulta|otra pregunta|quiero consultar otra cosa|empecemos de nuevo)"
_CONTEXT_RESET_RE = re.compile(rf"^\s*(?:(?:{_RESET_GREETING})\s*(?:bitey)?\s*[,;:\-]?\s*)?(?:{_RESET_ACTION})\s*[!.?]*\s*$|^\s*(?:{_RESET_GREETING})\s*(?:bitey)?\s*[!.?]*\s*$", re.I)

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

def _extract_pending_turn(response: str) -> dict[str, Any] | None:
    """Extract the last explicit question and numbered choices from Bitey's reply."""
    text = str(response or "").strip()
    if not text: return None
    options = []
    for line in text.splitlines():
        match = _OPTION_RE.match(line)
        if match: options.append({"number": int(match.group(1)), "text": match.group(2).strip()})
    question = None
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        if "?" in line: question = line; break
    if not question and options: question = next((line for line in lines if line.endswith(":") or "indica" in line.lower() or "qué" in line.lower()), None)
    if not question: return None
    lower = question.lower()
    if re.search(r"\b(qué|que)\b.*\b(ocurre|pasa|problema|s[ií]ntoma)\b|\b(describe|describa)\b.*\b(problema|ocurre|pasa)\b", lower): field = "symptom"
    elif re.search(r"\b(modelo|marca)\b", lower): field = "model"
    elif re.search(r"\b(windows|android|ios|sistema operativo|versi[oó]n)\b", lower): field = "os_version"
    elif re.search(r"\b(d[oó]nde|donde|ubicaci[oó]n|ubicacion)\b", lower): field = "location"
    elif re.search(r"\b(telefono|teléfono|móvil|movil|pc|computadora|impresora|router|c[aá]mara|cctv)\b", lower): field = "device"
    else: field = "unspecified"
    return {"field": field, "question": question, "options": options}

def _resolve_pending_reply(message: str, conversation: dict[str, Any] | None) -> tuple[str, dict[str, Any] | None]:
    text = str(message or "").strip()
    if not conversation: return text, None
    options = conversation.get("pending_options") or []
    if not isinstance(options, list) or not options: return text, None
    number = None
    match = re.fullmatch(r"(?:opci[oó]n\s*)?(\d{1,2})\s*[.)-]?", text, flags=re.I)
    if match: number = int(match.group(1))
    else:
        ordinal = {"primera":1,"primero":1,"segunda":2,"segundo":2,"tercera":3,"tercero":3,"cuarta":4,"cuarto":4}
        for word, value in ordinal.items():
            if re.search(rf"\b{word}\b", text, re.I): number = value; break
    if number is None: return text, None
    selected = next((item for item in options if int(item.get("number", -1)) == number), None)
    if not selected: return text, None
    question = str(conversation.get("pending_question") or "").strip()
    resolved = f"{text}\n[RESPUESTA CONTEXTUAL: el cliente seleccionó la opción {number}: {selected.get('text','')}. Esta respuesta corresponde a la pregunta pendiente: {question}]"
    return resolved, {"number": number, "text": selected.get("text", ""), "question": question, "field": conversation.get("pending_field")}

def _try_external_ai(*, company_id: int, message: str, channel: str, phone: str, email: str, customer_name: str, last_name: str, conversation_id: str | None, language: str, preferred_contact_channel: str | None) -> dict[str, Any]:
    identity_phone, external_identity = _channel_identity(channel, phone, conversation_id)
    customer = get_or_create_customer(company_id=company_id, phone=identity_phone, email=str(email or "").strip(), name=" ".join(x for x in (customer_name, last_name) if x).strip() or "Customer", channel=channel, external_id=external_identity)
    customer_id = customer.get("id") if isinstance(customer, dict) else None
    if not customer_id: return {"action":"conversation","create_ticket":False,"response":"No fue posible establecer la identidad de la conversación en este momento."}
    db_cid = _db_conversation_id(conversation_id) if channel in {"website", "app", "private", "api"} else None
    conversation = get_or_create_conversation(customer_id=customer_id, channel=channel, conversation_id=db_cid)
    cid = conversation.get("id") if isinstance(conversation, dict) else None
    reasoning_message, resolved_pending = _resolve_pending_reply(message, conversation)
    history = get_conversation_history(company_id=company_id, customer_id=customer_id, conversation_id=cid) if cid else []
    context_reset = bool(_CONTEXT_RESET_RE.match(str(message or "")))
    reasoning_history = [] if context_reset else history
    raw_state = build_problem_state(reasoning_history, reasoning_message)
    state = resolve_context(raw_state, reasoning_message, reasoning_history)
    if context_reset:
        state["active_problem"] = None
        state["active_category"] = None
        state["active_object"] = None
        state["active_model"] = None
        state["active_goal"] = None
        state["is_follow_up"] = False
    if resolved_pending:
        state["pending_answer"] = resolved_pending
        state["pending_question"] = {"field": resolved_pending.get("field"), "question": resolved_pending.get("question"), "options": conversation.get("pending_options") or []}
    memory = {"conversation_id":cid,"external_conversation_id":conversation_id,"history":reasoning_history,"recent_turns":state.get("recent_turns",[]),"confirmed_facts":state.get("confirmed_facts",[]),"last_service":None if context_reset else next((row.get("service_id") for row in reversed(history[-16:]) if row.get("service_id") is not None),None),"active_topic":state.get("active_category"),"active_object":state.get("active_object"),"active_model":state.get("active_model"),"active_problem":state.get("active_problem"),"active_goal":state.get("active_goal") or state.get("customer_goal"),"active_action":None,"active_location":state.get("active_location"),"active_url":None,"website_diagnostic_requested":state.get("website_diagnostic_requested",False),"stage":"diagnosis" if state.get("active_problem") else "exploration","is_follow_up":state.get("is_follow_up",False),"problem_state":state,"pending_turn":conversation.get("pending_question") if conversation else None,"current_message":message}
    if resolved_pending: memory["pending_answer"] = resolved_pending
    business_context = {"channel":channel,"active_goal":memory.get("active_goal"),"conversation":{"state":state.get("state"),"active_goal":memory.get("active_goal"),"active_problem":state.get("active_problem"),"active_category":state.get("active_category"),"active_object":state.get("active_object"),"active_model":state.get("active_model"),"active_location":state.get("active_location"),"symptoms":state.get("symptoms",[]),"hypotheses":state.get("hypotheses",[]),"customer_goal":state.get("customer_goal"),"confidence":state.get("confidence"),"confirmed_facts":state.get("confirmed_facts",[]),"pending_turn":memory.get("pending_turn"),"pending_answer":memory.get("pending_answer")}}
    if website_context := _website_context(reasoning_history, reasoning_message, state): business_context["website_context"] = website_context; business_context["website_diagnostic"] = bool(website_context.get("diagnostic_requested"))
    result = ai_first_decision(company_id=company_id, customer=customer, message=reasoning_message, intent={}, knowledge=None, memory=memory, language=language, business_context=business_context)
    if not isinstance(result,dict): return {"action":"conversation","create_ticket":False,"response":"No fue posible completar la consulta en este momento."}
    response=str(result.get("response") or "").strip(); result_service_id=result.get("service_id") or memory.get("last_service"); result_intent=result.get("intent")
    if cid:
        save_customer_message(company_id=company_id,customer_id=customer_id,conversation_id=cid,message=message,channel=channel,service_id=result_service_id)
        if response: save_bitey_message(company_id=company_id,customer_id=customer_id,conversation_id=cid,response=response,channel=channel,service_id=result_service_id)
        pending = _extract_pending_turn(response)
        if pending: update_conversation_context(cid,intent=result_intent,response=response,service_id=result_service_id,language=language,pending_field=pending["field"],pending_question=pending["question"],pending_options=pending["options"])
        else: update_conversation_context(cid,intent=result_intent,response=response,service_id=result_service_id,language=language,pending_field=None,pending_question=None,pending_options=[])
    result["conversation_id"]=cid; result["external_conversation_id"]=conversation_id; result["customer_id"]=customer_id
    if preferred_contact_channel: result["preferred_contact_channel"]=preferred_contact_channel
    return result

def handle_message(*, company_id: int, message: str, channel: str = "website", phone: str = "", email: str = "", customer_name: str = "Customer", last_name: str = "", conversation_id: str | None = None, language_preference: str = "auto", preferred_contact_channel: str | None = None) -> dict[str, Any]:
    normalized_channel = normalize_channel(channel)
    if not str(message or "").strip(): return _public_result({"success":False,"response":"Escribe un mensaje para continuar."})
    if normalized_channel == "whatsapp":
        from app.core.bitey import process_message
        result = process_message(company_id=company_id,message=str(message).strip(),phone=phone,email=email,customer_name=customer_name,last_name=last_name,channel="whatsapp",conversation_id=conversation_id,language_preference=language_preference)
        return _public_result(result)
    language = language_preference if language_preference not in (None,"","auto") else "es"
    result = _try_external_ai(company_id=company_id,message=str(message).strip(),channel=normalized_channel,phone=phone,email=email,customer_name=customer_name,last_name=last_name,conversation_id=conversation_id,language=language,preferred_contact_channel=preferred_contact_channel)
    return _public_result(result)
