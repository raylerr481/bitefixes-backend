"""
Bitey Message Service V7

Responsibilities:
- Save customer messages
- Save Bitey AI responses
- Compatible with Bitey Core
- Compatible with Supabase messages table

Does NOT:
- Detect intent
- Create tickets
- Manage workflows
"""

from typing import Optional
from app.database.supabase import database


def save_customer_message(
    company_id: int,
    customer_id: int,
    message: str,
    channel: str = "website",
    intent: Optional[str] = None,
    service_id: Optional[int] = None,
    confidence: Optional[int] = None,
    ticket_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
):
    """
    Save customer message into messages table.
    """

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

            "confidence": confidence,

            "ticket_id": ticket_id,

            "conversation_id": conversation_id

        }


        result = (
            database
            .table("messages")
            .insert(data)
            .execute()
        )


        print(
            "[CUSTOMER MESSAGE SAVED]",
            result.data
        )


        return result.data


    except Exception as error:

        print(
            "[SAVE CUSTOMER MESSAGE ERROR]",
            error
        )

        return None



def save_bitey_message(
    company_id: int,
    customer_id: int,
    response: Optional[str] = None,
    response_text: Optional[str] = None,
    channel: str = "website",
    intent: Optional[str] = None,
    service_id: Optional[int] = None,
    confidence: Optional[int] = None,
    ticket_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
):
    """
    Save Bitey AI response.

    Accepts:
    response=
    response_text=

    Both are supported for compatibility.
    """

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

            "confidence": confidence,

            "ticket_id": ticket_id,

            "conversation_id": conversation_id

        }


        result = (
            database
            .table("messages")
            .insert(data)
            .execute()
        )


        print(
            "[BITEY MESSAGE SAVED]",
            result.data
        )


        return result.data


    except Exception as error:

        print(
            "[SAVE BITEY MESSAGE ERROR]",
            error
        )

        return None