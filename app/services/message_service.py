"""Bitey Message Service V8

Persists conversation messages while normalizing AI confidence to the
integer percentage expected by the existing Supabase messages schema.
"""
from typing import Optional, Union
import math
from app.database.supabase import database


def _confidence_percent(value: Optional[Union[int, float, str]]) -> Optional[int]:
    """Return confidence as an integer percentage for the messages table.

    Bitey's reasoning layer uses 0..1 confidence. Older database schemas store
    an integer percentage (0..100). Accept both representations so provider
    changes cannot break persistence.
    """
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    if 0.0 <= number <= 1.0:
        number *= 100.0
    return max(0, min(100, int(round(number))))


def save_customer_message(
    company_id: int,
    customer_id: int,
    message: str,
    channel: str = "website",
    intent: Optional[str] = None,
    service_id: Optional[int] = None,
    confidence: Optional[Union[int, float, str]] = None,
    ticket_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
):
    try:
        data = {
            "company_id": company_id,
            "customer_id": customer_id,
            "sender_type": "customer",
            "message_content": message,
            "channel": channel,
            "message_type": "text",
            "intent": intent,
            "service_id": service_id,
            "confidence": _confidence_percent(confidence),
            "ticket_id": ticket_id,
            "conversation_id": conversation_id,
        }
        result = database.table("messages").insert(data).execute()
        print("[CUSTOMER MESSAGE SAVED]", result.data)
        return result.data
    except Exception as error:
        print("[SAVE CUSTOMER MESSAGE ERROR]", error)
        return None


def save_bitey_message(
    company_id: int,
    customer_id: int,
    response: Optional[str] = None,
    response_text: Optional[str] = None,
    channel: str = "website",
    intent: Optional[str] = None,
    service_id: Optional[int] = None,
    confidence: Optional[Union[int, float, str]] = None,
    ticket_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
):
    """Persist Bitey's response without allowing confidence types to leak to DB."""
    try:
        if response is None:
            response = response_text
        data = {
            "company_id": company_id,
            "customer_id": customer_id,
            "sender_type": "ai",
            "message_content": response,
            "ai_response": response,
            "channel": channel,
            "message_type": "text",
            "intent": intent,
            "service_id": service_id,
            "confidence": _confidence_percent(confidence),
            "ticket_id": ticket_id,
            "conversation_id": conversation_id,
        }
        result = database.table("messages").insert(data).execute()
        print("[BITEY MESSAGE SAVED]", result.data)
        return result.data
    except Exception as error:
        print("[SAVE BITEY MESSAGE ERROR]", error)
        return None
