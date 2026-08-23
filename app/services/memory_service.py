"""
Bitey Memory Service V2

Customer conversational memory layer.

Handles:
- Message history
- Last intent
- Last service
- Last ticket
- Previous AI responses
"""

from app.database.supabase import supabase


def get_memory_context(customer_id: int, conversation_id=None, limit: int = 20):
    """Return memory strictly scoped to the active conversation.

    Bitey Core prefers this function when it is available. This prevents a
    customer's older, unrelated conversations from becoming cognitive context
    for the current turn while keeping the existing customer-wide fallback.
    """
    if conversation_id in (None, ""):
        return {}
    try:
        result = (
            supabase.table("messages").select("*")
            .eq("customer_id", customer_id)
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=True)
            .limit(max(1, min(limit, 30)))
            .execute()
        )
        messages = result.data or []
        history = list(reversed(messages))
        last = history[-1] if history else {}
        return {
            "history": history,
            "last_intent": last.get("intent"),
            "last_service": last.get("service_id"),
            "last_ticket": last.get("ticket_id"),
            "last_confidence": last.get("confidence"),
            "total_messages": len(history),
            "conversation_id": conversation_id,
            "scope": "conversation",
        }
    except Exception as error:
        print("[MEMORY CONTEXT ERROR]", type(error).__name__)
        return {
            "history": [],
            "last_intent": None,
            "last_service": None,
            "last_ticket": None,
            "last_confidence": None,
            "total_messages": 0,
            "conversation_id": conversation_id,
            "scope": "conversation",
        }


def get_customer_memory(company_id:int, customer_id:int, limit:int=20):
    try:
        result = (
            supabase.table("messages").select("*")
            .eq("company_id", company_id).eq("customer_id", customer_id)
            .order("created_at", desc=True).limit(limit).execute()
        )
        messages = result.data or []
        history = list(reversed(messages))
        last = history[-1] if history else {}
        return {
            "history": history,
            "last_intent": last.get("intent"),
            "last_service": last.get("service_id"),
            "last_ticket": last.get("ticket_id"),
            "total_messages": len(history)
        }
    except Exception as error:
        print("[MEMORY ERROR]", error)
        return {"history": [], "last_intent": None, "last_service": None, "last_ticket": None, "total_messages": 0}


def get_memory_state(customer_id:int, company_id:int = 1):
    """Compatibility function for Bitey Core."""
    return get_customer_memory(company_id, customer_id)


def get_last_customer_message(company_id:int, customer_id:int):
    try:
        result = (
            supabase.table("messages").select("*")
            .eq("company_id", company_id).eq("customer_id", customer_id)
            .eq("sender_type", "customer").order("created_at", desc=True)
            .limit(1).execute()
        )
        return result.data[0] if result.data else None
    except Exception as error:
        print("[MEMORY ERROR]", error)
        return None


def get_last_ai_response(company_id:int, customer_id:int):
    try:
        result = (
            supabase.table("messages").select("*")
            .eq("company_id", company_id).eq("customer_id", customer_id)
            .eq("sender_type", "bitey").order("created_at", desc=True)
            .limit(1).execute()
        )
        return result.data[0] if result.data else None
    except Exception as error:
        print("[MEMORY ERROR]", error)
        return None


def customer_has_history(company_id:int, customer_id:int):
    try:
        result = (
            supabase.table("messages").select("id")
            .eq("company_id", company_id).eq("customer_id", customer_id)
            .limit(1).execute()
        )
        return bool(result.data)
    except Exception:
        return False
