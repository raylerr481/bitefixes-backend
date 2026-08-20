"""BiteFixes conversation lifecycle and context persistence."""

from datetime import datetime, timezone
from typing import Any

from app.database.supabase import database


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_or_create_conversation(customer_id: int, channel: str = "website", conversation_id: Any = None):
    """Resolve an active conversation, scoped to the authenticated customer."""
    try:
        query = database.table("conversations").select("*").eq("customer_id", customer_id).eq("status", "active")
        if conversation_id not in (None, ""):
            query = query.eq("id", conversation_id)
        result = query.limit(1).execute()
        if result.data:
            return result.data[0]

        # Never fall back to another conversation when an explicit ID is supplied.
        conversation = {
            "customer_id": customer_id,
            "channel": channel or "website",
            "status": "active",
            "agent": "bitey",
            "handled_by_ai": True,
            "requires_human": False,
            "created_at": _now(),
        }
        result = database.table("conversations").insert(conversation).execute()
        return result.data[0] if result.data else None
    except Exception as error:
        print("[CREATE CONVERSATION ERROR]", type(error).__name__, error)
        return None


def get_conversation(conversation_id: Any, customer_id: int | None = None):
    try:
        query = database.table("conversations").select("*").eq("id", conversation_id)
        if customer_id is not None:
            query = query.eq("customer_id", customer_id)
        result = query.limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as error:
        print("[GET CONVERSATION ERROR]", type(error).__name__, error)
        return None


def update_conversation(conversation_id: Any, data: dict):
    try:
        allowed_fields = {
            "ticket_id", "agent", "last_intent", "last_response", "last_service",
            "last_confidence", "handled_by_ai", "requires_human", "status",
            "closed_at", "language", "updated_at",
        }
        clean_data = {k: v for k, v in data.items() if k in allowed_fields}
        if not clean_data:
            return None
        clean_data["updated_at"] = _now()
        result = database.table("conversations").update(clean_data).eq("id", conversation_id).execute()
        return result.data[0] if result.data else None
    except Exception as error:
        print("[UPDATE CONVERSATION ERROR]", type(error).__name__, error)
        return None


def close_conversation(conversation_id: Any):
    return update_conversation(conversation_id, {"status": "closed", "closed_at": _now()})


def update_conversation_context(conversation_id: Any, intent: str = None, response: str = None, ticket_id: int = None, service_id: int = None, confidence: float = None, language: str = None):
    data = {}
    if intent:
        data["last_intent"] = intent
    if response:
        data["last_response"] = response
    if ticket_id is not None:
        data["ticket_id"] = ticket_id
    if service_id is not None:
        data["last_service"] = service_id
    if confidence is not None:
        data["last_confidence"] = float(confidence)
    if language:
        data["language"] = language
    return update_conversation(conversation_id, data)


# Backwards-compatible aliases.
def obtener_o_crear_conversacion(customer_id, channel="website"):
    return get_or_create_conversation(customer_id, channel)


def actualizar_conversacion(conversation_id, datos):
    return update_conversation(conversation_id, datos)


def cerrar_conversacion(conversation_id):
    return close_conversation(conversation_id)
