"""BiteFixes message persistence compatible with the canonical Supabase conversation schema."""
from typing import Optional, Union
import math
from app.database.supabase import database

def _confidence_percent(value: Optional[Union[int, float, str]]) -> Optional[int]:
    if value is None or value == "": return None
    try: number = float(value)
    except (TypeError, ValueError): return None
    if not math.isfinite(number): return None
    if 0.0 <= number <= 1.0: number *= 100.0
    return max(0, min(100, int(round(number))))

def _save(data: dict, role: str):
    # Canonical schema requires role/content; BiteFixes compatibility fields are retained.
    data["role"] = role
    data["content"] = data.get("message_content") or ""
    return database.table("messages").insert(data).execute().data

def save_customer_message(company_id: int, customer_id: int, message: str, channel: str = "website",
                          intent: Optional[str] = None, service_id: Optional[int] = None,
                          confidence: Optional[Union[int, float, str]] = None, ticket_id: Optional[int] = None,
                          conversation_id=None):
    try:
        data = {"company_id": company_id, "customer_id": customer_id, "sender_type": "customer",
                "message_content": message, "channel": channel, "message_type": "text", "intent": intent,
                "service_id": service_id, "confidence": _confidence_percent(confidence), "ticket_id": ticket_id,
                "conversation_id": conversation_id}
        return _save(data, "user")
    except Exception as error:
        print("[SAVE CUSTOMER MESSAGE ERROR]", type(error).__name__, error); return None

def save_bitey_message(company_id: int, customer_id: int, response: Optional[str] = None,
                       response_text: Optional[str] = None, channel: str = "website",
                       intent: Optional[str] = None, service_id: Optional[int] = None,
                       confidence: Optional[Union[int, float, str]] = None, ticket_id: Optional[int] = None,
                       conversation_id=None):
    try:
        if response is None: response = response_text
        data = {"company_id": company_id, "customer_id": customer_id, "sender_type": "ai",
                "message_content": response, "ai_response": response, "channel": channel,
                "message_type": "text", "intent": intent, "service_id": service_id,
                "confidence": _confidence_percent(confidence), "ticket_id": ticket_id,
                "conversation_id": conversation_id}
        return _save(data, "assistant")
    except Exception as error:
        print("[SAVE BITEY MESSAGE ERROR]", type(error).__name__, error); return None

def get_conversation_history(*, company_id: int, customer_id: int, conversation_id, limit: int = 12):
    """Return recent turns chronologically for reasoning."""
    try:
        rows = (database.table("messages").select(
            "sender_type,message_content,ai_response,intent,service_id,created_at,role,content"
        ).eq("company_id", company_id).eq("customer_id", customer_id)
         .eq("conversation_id", conversation_id).order("created_at", desc=True)
         .limit(max(1, min(limit, 30))).execute().data or [])
        rows.reverse(); return rows
    except Exception as error:
        print("[HISTORY ERROR]", type(error).__name__, error); return []
