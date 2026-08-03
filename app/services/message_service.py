"""
BiteFixes Message Service

Handles:
- Customer messages
- Bitey AI responses

Database:
messages
"""

from app.database.supabase import database


def save_customer_message(
    company_id,
    customer_id,
    conversation_id,
    message,
    channel="website",
    intent=None,
    confidence=0
):

    try:

        data = {
            "company_id": company_id,
            "customer_id": customer_id,
            "conversation_id": conversation_id,

            "sender_type": "customer",

            "message_content": message,

            "channel": channel,

            "message_type": "text",

            "intent": intent,

            "service_id": None,

            "ticket_id": None,

            "confidence": confidence,

            "ai_response": None
        }


        response = (
            database
            .table("messages")
            .insert(data)
            .execute()
        )


        return response.data


    except Exception as error:

        print(
            "[MESSAGE CUSTOMER ERROR]",
            error
        )

        return None



def save_bitey_message(
    company_id,
    customer_id,
    conversation_id,
    response,

    intent=None,
    confidence=0,

    service_id=None,
    ticket_id=None,

    channel="website"
):

    try:

        data = {

            "company_id": company_id,

            "customer_id": customer_id,

            "conversation_id": conversation_id,


            "sender_type": "bitey",


            "message_content": response,


            "channel": channel,


            "message_type": "text",


            "intent": intent,


            "service_id": service_id,


            "ticket_id": ticket_id,


            "confidence": confidence,


            "ai_response": response

        }


        result = (
            database
            .table("messages")
            .insert(data)
            .execute()
        )


        return result.data


    except Exception as error:

        print(
            "[MESSAGE BITEY ERROR]",
            error
        )

        return None