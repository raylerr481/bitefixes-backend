"""
BiteFixes Conversation Service

Handles:
- Create conversations
- Retrieve active conversation
- Update conversation memory
- Close conversations

Supabase table:
conversations
"""


from datetime import datetime

from app.database.supabase import database



def get_or_create_conversation(
    customer_id:int,
    channel:str="website"
):

    try:


        # Search active conversation

        result = (

            database
            .table("conversations")
            .select("*")
            .eq(
                "customer_id",
                customer_id
            )
            .eq(
                "status",
                "active"
            )
            .limit(1)
            .execute()

        )


        if result.data:

            return result.data[0]



        # Create new conversation

        conversation = {


            "customer_id": customer_id,


            "channel": channel,


            "status": "active",


            "agent": "bitey",


            "handled_by_ai": True,


            "requires_human": False,


            "created_at":
                datetime.utcnow().isoformat()

        }



        result = (

            database
            .table("conversations")
            .insert(conversation)
            .execute()

        )



        if result.data:

            return result.data[0]



        return None



    except Exception as error:


        print(
            "[CREATE CONVERSATION ERROR]",
            error
        )


        return None





def get_conversation(
    conversation_id:int
):

    try:


        result = (

            database
            .table("conversations")
            .select("*")
            .eq(
                "id",
                conversation_id
            )
            .limit(1)
            .execute()

        )


        if result.data:

            return result.data[0]


        return None



    except Exception as error:


        print(
            "[GET CONVERSATION ERROR]",
            error
        )


        return None





def update_conversation(
    conversation_id:int,
    data:dict
):

    try:


        # Only valid columns

        allowed = {


            "ticket_id",
            "agent",
            "last_intent",
            "last_response",
            "handled_by_ai",
            "requires_human",
            "status",
            "closed_at"

        }



        clean_data = {

            key:value

            for key,value in data.items()

            if key in allowed

        }



        result = (

            database
            .table("conversations")
            .update(clean_data)
            .eq(
                "id",
                conversation_id
            )
            .execute()

        )



        if result.data:

            return result.data[0]



        return None



    except Exception as error:


        print(
            "[UPDATE CONVERSATION ERROR]",
            error
        )


        return None





def close_conversation(
    conversation_id:int
):

    return update_conversation(

        conversation_id,

        {

            "status":"closed",

            "closed_at":
                datetime.utcnow().isoformat()

        }

    )





# Compatibility aliases


def obtener_o_crear_conversacion(
    customer_id,
    channel="website"
):

    return get_or_create_conversation(

        customer_id,

        channel

    )



def actualizar_conversacion(
    conversation_id,
    datos
):

    return update_conversation(

        conversation_id,

        datos

    )



def cerrar_conversacion(
    conversation_id
):

    return close_conversation(

        conversation_id

    )