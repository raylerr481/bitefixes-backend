"""
Bitey Ticket Service V8

Gestiona:
- creación de tickets
- búsqueda de tickets abiertos
- historial del cliente
"""


from app.database.supabase import database



def get_customer_tickets(
    customer_id:int,
    company_id:int = 1
):

    try:

        result = (

            database
            .table("tickets")
            .select("*")
            .eq(
                "customer_id",
                customer_id
            )
            .eq(
                "company_id",
                company_id
            )
            .order(
                "created_at",
                desc=True
            )
            .execute()

        )


        return result.data or []


    except Exception as error:


        print(
            "[GET CUSTOMER TICKETS ERROR]",
            error
        )


        return []



def get_open_ticket(
    customer_id:int,
    company_id:int = 1,
    intent:str=None
):

    tickets = get_customer_tickets(
        customer_id,
        company_id
    )


    for ticket in tickets:

        if ticket.get(
            "status"
        ) != "open":

            continue


        if intent:

            if ticket.get(
                "intent"
            ) == intent:

                return ticket

        else:

            return ticket



    return None



# compatibilidad Bitey anteriores


def buscar_ticket_abierto(
    customer_id,
    company_id=1,
    intent=None
):

    return get_open_ticket(
        customer_id,
        company_id,
        intent
    )



def crear_ticket(data:dict):

    try:

        result = (

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