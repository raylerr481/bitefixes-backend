"""
Bitey Context Service V8

Customer intelligence layer.

Creates:

- Customer profile
- Service history
- Active ticket
- Last intent
- Conversation summary
"""

from app.supabase_client import supabase



def get_customer(
    customer_id:int,
    company_id:int
):

    result=(

        supabase
        .table("customers")
        .select("*")
        .eq(
            "id",
            customer_id
        )
        .eq(
            "company_id",
            company_id
        )
        .execute()

    )

    return (
        result.data[0]
        if result.data
        else None
    )





def get_customer_tickets(
    customer_id:int
):

    result=(

        supabase
        .table("tickets")
        .select("*")
        .eq(
            "customer_id",
            customer_id
        )
        .order(
            "created_at",
            desc=True
        )
        .execute()

    )


    return result.data or []





def get_recent_messages(
    customer_id:int,
    limit:int=20
):

    result=(

        supabase
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
        .limit(limit)
        .execute()

    )


    return list(
        reversed(
            result.data or []
        )
    )





def get_last_intent(
    messages,
    tickets
):


    for message in reversed(messages):

        intent=message.get(
            "intent"
        )

        if intent:

            return intent



    for ticket in tickets:

        intent=ticket.get(
            "intent"
        )

        if intent:

            return intent



    return None





def get_active_ticket(
    tickets
):

    for ticket in tickets:

        if ticket.get(
            "status"
        )=="open":

            return {

                "id":
                    ticket.get("id"),

                "code":
                    ticket.get("ticket_code"),

                "title":
                    ticket.get("title"),

                "service_id":
                    ticket.get("service_id"),

                "intent":
                    ticket.get("intent")

            }


    return None





def get_previous_services(
    tickets
):

    services=[]


    for ticket in tickets:


        intent=ticket.get(
            "intent"
        )


        if intent and intent not in services:

            services.append(
                intent
            )


    return services[:10]





def build_customer_context(
    customer_id:int,
    company_id:int
):


    customer=get_customer(
        customer_id,
        company_id
    )


    tickets=get_customer_tickets(
        customer_id
    )


    messages=get_recent_messages(
        customer_id
    )



    memory={


        "customer":{

            "name":
                customer.get(
                    "full_name"
                )
                if customer
                else None,


            "language":
                customer.get(
                    "preferred_language"
                )
                if customer
                else None

        },


        "profile":

            "Returning customer"
            if len(tickets)>=3
            else "New customer",


        "active_ticket":

            get_active_ticket(
                tickets
            ),


        "previous_services":

            get_previous_services(
                tickets
            ),


        "last_intent":

            get_last_intent(
                messages,
                tickets
            )

    }


    return {

        "summary":memory,

        "customer":customer,

        "tickets":tickets,

        "messages":messages

    }