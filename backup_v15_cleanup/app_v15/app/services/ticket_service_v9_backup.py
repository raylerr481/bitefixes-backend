"""
Bitey Ticket Service V8

Responsible for:

- Create tickets
- Avoid duplicates
- Find active tickets
- Ticket lifecycle
"""

from datetime import datetime

from app.database.supabase import database



def create_ticket(
    customer_id:int,
    service_id=None,
    description="",
    title="Bitey Request",
    intent=None,
    company_id=1,
    channel="website",
    ticket_type="support"
):

    try:

        data={

            "company_id":company_id,

            "customer_id":customer_id,

            "service_id":service_id,

            "title":title,

            "description":description,

            "intent":intent,

            "status":"open",

            "priority":"medium",

            "channel":channel,

            "ticket_type":ticket_type,

            "language":"pt",

            "created_at":
                datetime.utcnow().isoformat()

        }


        result=(
            database
            .table("tickets")
            .insert(data)
            .execute()
        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            "[CREATE TICKET ERROR]",
            error
        )

        return None





def get_open_ticket(
    customer_id:int,
    service_id=None,
    intent=None
):

    try:


        result=(

            database
            .table("tickets")
            .select("*")
            .eq(
                "customer_id",
                customer_id
            )
            .eq(
                "status",
                "open"
            )
            .order(
                "created_at",
                desc=True
            )
            .execute()

        )


        tickets=result.data or []


        for ticket in tickets:


            if service_id:

                if ticket.get(
                    "service_id"
                ) != service_id:

                    continue



            if intent:

                if ticket.get(
                    "intent"
                ) != intent:

                    continue



            return ticket



        return None



    except Exception as error:


        print(
            "[OPEN TICKET ERROR]",
            error
        )

        return None





def get_ticket(ticket_id:int):

    try:

        result=(

            database
            .table("tickets")
            .select("*")
            .eq(
                "id",
                ticket_id
            )
            .execute()

        )


        return (
            result.data[0]
            if result.data
            else None
        )


    except Exception as error:

        print(
            "[GET TICKET ERROR]",
            error
        )

        return None





def update_ticket(
    ticket_id:int,
    data:dict
):

    try:

        result=(

            database
            .table("tickets")
            .update(data)
            .eq(
                "id",
                ticket_id
            )
            .execute()

        )


        return (
            result.data[0]
            if result.data
            else None
        )


    except Exception as error:

        print(
            "[UPDATE ERROR]",
            error
        )

        return None





def close_ticket(ticket_id):

    return update_ticket(
        ticket_id,
        {
            "status":"closed"
        }
    )
# =====================================================
# COMPATIBILITY ALIAS
# =====================================================

def find_open_ticket(
    customer_id: int,
    intent: str = None,
    service_id: int = None
):
    """
    Compatibility wrapper.
    Old Bitey Core compatibility.
    """

    return get_open_ticket(
        customer_id=customer_id,
        service_id=service_id,
        intent=intent
    )