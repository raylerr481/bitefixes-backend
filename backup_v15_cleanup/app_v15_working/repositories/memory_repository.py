"""
Memory Repository

Database access layer for chat history.

Responsibilities:
- Save messages
- Update message intent
- Get conversation history
- Get last message
- Delete conversation history

Multi-company SaaS ready.
"""

from datetime import datetime, timezone

from app.database.supabase import supabase


DEFAULT_COMPANY_ID = 1


# =====================================================
# INTERNAL
# =====================================================

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================
# SAVE MESSAGE
# =====================================================

def save(
    company_id: int,
    customer_id: int,
    message: str,
    role: str,
    intent: str | None = None,
    service_id: int | None = None,
    ticket_id: int | None = None,
    channel: str = "web",
):

    data = {

        "empresa_id": company_id,

        "cliente_id": customer_id,

        "mensaje": message,

        "rol": role,

        "remitente": None,

        "canal": channel,

        "intencion": intent,

        "servicio_id": service_id,

        "ticket_id": ticket_id,

        "tipo_mensaje": "texto",

        "created_at": _now(),
    }

    result = (
        supabase
        .table("historial_chats")
        .insert(data)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


# =====================================================
# UPDATE MESSAGE
# =====================================================

def update_intent(
    message_id: int,
    intent: str,
    service_id: int | None,
):

    data = {

        "intencion": intent,

        "servicio_id": service_id,
    }

    result = (
        supabase
        .table("historial_chats")
        .update(data)
        .eq("id", message_id)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


# =====================================================
# GET MEMORY
# =====================================================

def get_history(
    customer_id: int,
    company_id: int,
    limit: int = 20,
):

    result = (
        supabase
        .table("historial_chats")
        .select("*")
        .eq("empresa_id", company_id)
        .eq("cliente_id", customer_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return result.data or []


# =====================================================
# LAST MESSAGE
# =====================================================

def get_last(
    customer_id: int,
    company_id: int,
):

    history = get_history(
        customer_id,
        company_id,
        1,
    )

    if history:
        return history[0]

    return None


# =====================================================
# DELETE MEMORY
# =====================================================

def delete_history(
    customer_id: int,
    company_id: int,
):

    (
        supabase
        .table("historial_chats")
        .delete()
        .eq("empresa_id", company_id)
        .eq("cliente_id", customer_id)
        .execute()
    )

    return True