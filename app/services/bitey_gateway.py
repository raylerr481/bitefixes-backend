"""Bitey Cloud Gateway - AI-first, context-first facade for every channel."""
from __future__ import annotations
import os
from typing import Any
from app.core.bitey import process_message
from app.services.decision_engine_v29 import decision_engine as ai_first_decision
from app.services.customer_service import get_or_create_customer
from app.services.conversation_service import get_or_create_conversation
from app.services.message_service import save_customer_message, save_bitey_message, get_conversation_history

SUPPORTED_CHANNELS = {"website", "whatsapp", "messenger", "telegram", "email", "sms", "phone", "app", "private", "api"}
_INTERNAL_KEYS = {"intent", "confidence", "raw_intent_score", "knowledge", "knowledge_found", "memory", "ai_consultation", "comparative_evaluation", "response_source", "decision", "gateway_debug"}
_GREETING_WORDS = {"hola", "hello", "hi", "hey", "oi", "ola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "bom dia", "boa tarde", "boa noite"}


def normalize_channel(channel: str | None) -> str:
    value = str(channel or "website").strip().lower(); return value if value in SUPPORTED_CHANNELS else "api"


def _public_result(result: dict[str, Any]) -> dict[str, Any]:
    if os.getenv("BITEY_PUBLIC_DEBUG", "false").lower() == "true": return result
    public = {k: v for k, v in result.items() if k not in _INTERNAL_KEYS}; public["public_contract"] = "bitey-chat-v1"; return public


def _try_ai_first(*, company_id: int, message: str, channel: str, customer_name: str,
                  last_name: str, conversation_id: str | None, language: str) -> dict[str, Any] | None:
    try:
        phone = f"web:{conversation_id}" if conversation_id else "web"
        customer = get_or_create_customer(company_id=company_id, phone=phone, email="",
                                           name=" ".join(x for x in (customer_name, last_name) if x).strip() or "Customer")
        customer_id = customer.get("id") if isinstance(customer, dict) else None
        if not customer_id: return None
        conversation = get_or_create_conversation(customer_id=customer_id, channel=channel, conversation_id=conversation_id)
        cid = conversation.get("id") if isinstance(conversation, dict) else None
        history = get_conversation_history(company_id=company_id, customer_id=customer_id, conversation_id=cid) if cid else []
        last_service = next((row.get("service_id") for row in reversed(history) if row.get("service_id") is not None), None)
        memory = {"conversation_id": cid, "history": history, "last_service": last_service,
                  "active_topic": None, "active_object": None, "stage": "exploration"}
        result = ai_first_decision(company_id=company_id, customer=customer, message=message, intent={}, knowledge=None,
                                   memory=memory, language=language, business_context=None)
        if not isinstance(result, dict) or result.get("action") != "conversation" or result.get("create_ticket"): return None
        response = str(result.get("response") or "").strip()
        if not response: return None
        if cid:
            save_customer_message(company_id=company_id, customer_id=customer_id, conversation_id=cid, message=message, channel=channel)
            save_bitey_message(company_id=company_id, customer_id=customer_id, conversation_id=cid, response=response, channel=channel)
        result["conversation_id"] = cid; result["customer_id"] = customer_id
        result["gateway"] = {"channel": channel, "architecture": "bitey-ai-first-v30-context-first"}
        return result
    except Exception as exc:
        print("[AI-FIRST GATEWAY WARNING]", type(exc).__name__); return None


def handle_message(*, company_id: int, message: str, channel: str = "website", phone: str = "", email: str = "",
                   customer_name: str = "Customer", last_name: str = "", conversation_id: str | None = None,
                   language_preference: str = "auto", preferred_contact_channel: str | None = None) -> dict[str, Any]:
    normalized_channel = normalize_channel(channel)
    language = language_preference if language_preference not in (None, "", "auto") else "es"
    text = str(message or "").strip().lower()
    if text not in _GREETING_WORDS:
        ai_first = _try_ai_first(company_id=company_id, message=message, channel=normalized_channel,
                                 customer_name=customer_name, last_name=last_name, conversation_id=conversation_id, language=language)
        if ai_first: return _public_result(ai_first)
        return _public_result({"action": "conversation", "create_ticket": False,
            "requires_quote": False,
            "response": "Claro. Cuéntame un poco más sobre lo que necesitas y te ayudo dentro del contexto y los servicios de esta empresa.",
            "conversation_stage": "exploration",
            "metadata": {"architecture": "bitey-ai-first-v30-context-first", "fallback": "safe_conversation", "cognitive_authority": "external_ai"}})

    result = process_message(company_id=company_id, message=message, phone=phone or "", email=email or "",
                             customer_name=customer_name or "Customer", last_name=last_name or "", channel=normalized_channel,
                             conversation_id=conversation_id, language_preference=language_preference)
    if not isinstance(result, dict): return {"success": False, "response": "No fue posible procesar la solicitud.", "public_contract": "bitey-chat-v1"}
    public = _public_result(result); public["gateway"] = {"channel": normalized_channel, "architecture": "bitey-ai-first-v30-context-first"}
    if preferred_contact_channel: public["preferred_contact_channel"] = preferred_contact_channel
    return public
