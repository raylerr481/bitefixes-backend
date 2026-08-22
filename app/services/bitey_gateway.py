"""Bitey Cloud Gateway - one identical AI/context flow for every channel."""
from __future__ import annotations
import os
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
    public["public_contract"] = "bitey-chat-v1"
    return public


def _conversation_key(channel: str, conversation_id: str | None) -> str:
    """Stable external identity for channels without a phone/email identifier."""
    return f"{channel}:{conversation_id}" if conversation_id else f"{channel}:anonymous"


def _db_conversation_id(value: str | None) -> int | None:
    """Only PostgreSQL conversation primary keys are passed as DB IDs.

    WhatsApp/Telegram/web sessions commonly use UUIDs or provider IDs. Those
    are channel identities, not the integer conversations.id primary key.
    """
    try:
        if value in (None, ""):
            return None
        text = str(value).strip()
        if text.isdigit():
            return int(text)
    except (TypeError, ValueError):
        pass
    return None


def _try_external_ai(*, company_id: int, message: str, channel: str, phone: str,
                     email: str, customer_name: str, last_name: str,
                     conversation_id: str | None, language: str,
                     preferred_contact_channel: str | None) -> dict[str, Any]:
    """Run exactly one cognitive path, regardless of channel.

    External AI creates the final cognitive response. Bitey transports context,
    memory, tools and persistence; it never falls back to a locally generated
    cognitive answer when the external AI is unavailable.
    """
    # Preserve real customer identity when a channel provides it. For channels
    # without phone/email, use a stable channel/provider identity so repeated
    # webhook events resolve to the same customer.
    identity_phone = str(phone or "").strip() or _conversation_key(channel, conversation_id)
    customer = get_or_create_customer(
        company_id=company_id,
        phone=identity_phone,
        email=str(email or "").strip(),
        name=" ".join(x for x in (customer_name, last_name) if x).strip() or "Customer",
    )
    customer_id = customer.get("id") if isinstance(customer, dict) else None
    if not customer_id:
        return {
            "action": "conversation", "create_ticket": False,
            "response": "La IA externa no pudo completar esta consulta porque no fue posible establecer la identidad de la conversación. El mensaje no se pierde.",
            "metadata": {"cognitive_authority": "external_ai", "operational_reason": "customer_identity_unavailable"},
        }

    db_cid = _db_conversation_id(conversation_id)
    conversation = get_or_create_conversation(customer_id=customer_id, channel=channel, conversation_id=db_cid)
    cid = conversation.get("id") if isinstance(conversation, dict) else None
    history = get_conversation_history(company_id=company_id, customer_id=customer_id, conversation_id=cid) if cid else []
    last_service = next((row.get("service_id") for row in reversed(history) if row.get("service_id") is not None), None)
    memory = {
        "conversation_id": cid,
        "external_conversation_id": conversation_id,
        "history": history,
        "last_service": last_service,
        "active_topic": None,
        "active_object": None,
        "stage": "exploration",
    }

    result = ai_first_decision(
        company_id=company_id, customer=customer, message=message, intent={},
        knowledge=None, memory=memory, language=language, business_context={"channel": channel}
    )
    if not isinstance(result, dict):
        return {"action": "conversation", "create_ticket": False,
                "response": "La IA externa no pudo completar esta consulta en este momento.",
                "metadata": {"cognitive_authority": "external_ai", "operational_reason": "invalid_ai_result"}}

    response = str(result.get("response") or "").strip()
    if cid:
        save_customer_message(company_id=company_id, customer_id=customer_id, conversation_id=cid, message=message, channel=channel)
        if response:
            save_bitey_message(company_id=company_id, customer_id=customer_id, conversation_id=cid, response=response, channel=channel)

    result["conversation_id"] = cid
    result["external_conversation_id"] = conversation_id
    result["customer_id"] = customer_id
    result["gateway"] = {
        "channel": channel,
        "architecture": "single-cognitive-flow-v31",
        "path": [
            "channel_input", "identity_resolution", "conversation_memory",
            "business_context", "governed_research", "external_ai_reasoning",
            "external_ai_final_response", "learning_storage", "channel_output",
        ],
        "cognitive_authority": "external_ai",
        "bitey_role": "communication_context_memory_apprentice_tools_persistence",
    }
    if preferred_contact_channel:
        result["preferred_contact_channel"] = preferred_contact_channel
    return result


def handle_message(*, company_id: int, message: str, channel: str = "website", phone: str = "", email: str = "",
                   customer_name: str = "Customer", last_name: str = "", conversation_id: str | None = None,
                   language_preference: str = "auto", preferred_contact_channel: str | None = None) -> dict[str, Any]:
    """Channel-neutral entry point. Every message uses the same external-AI path."""
    normalized_channel = normalize_channel(channel)
    language = language_preference if language_preference not in (None, "", "auto") else "es"
    if not str(message or "").strip():
        return _public_result({"success": False, "response": "Escribe un mensaje para continuar."})
    result = _try_external_ai(
        company_id=company_id, message=str(message), channel=normalized_channel,
        phone=phone, email=email, customer_name=customer_name, last_name=last_name,
        conversation_id=conversation_id, language=language,
        preferred_contact_channel=preferred_contact_channel,
    )
    return _public_result(result)
