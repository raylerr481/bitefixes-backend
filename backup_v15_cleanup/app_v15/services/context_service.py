"""
Bitey Customer Context Service

Builds customer memory.

Used by:
Bitey Core
Decision Engine
AI responses
"""


from app.database.supabase import database



def build_customer_context(
    customer_id:int,
    company_id:int
):

    try:


        messages = (

            database
            .table("messages")
            .select("*")
            .eq(
                "customer_id",
                customer_id
            )
            .order(
                "created_at",
                desc=True
            )
            .limit(10)
            .execute()

        )


        history = messages.data or []



        summary = {

            "customer_id": customer_id,

            "company_id": company_id,

            "messages_count":
                len(history),

            "last_messages":
                history[:5]

        }



        return {


            "summary": summary,


            "history": history


        }



    except Exception as error:


        print(
            "[CONTEXT ERROR]",
            error
        )


        return {


            "summary": {},

            "history": []

        }