"""
BiteFixes Ticket Service

Central ticket lifecycle manager.

Features:
- Create tickets
- Find duplicated open tickets
- Update tickets
- Close tickets
- Cancel tickets

Supabase table:
tickets
"""

from datetime import datetime
from app.database.supabase import database


def create_ticket(
    customer_id: int,
    service_id=None,
    description: str = "",
    title: str = "New Ticket",
    intent: str = None,
    company_id: int = 1,
    channel: str = "website",
    ticket_type: str = "support"
):

    try:

        ticket = {

            "company_id": company_id,

            "customer_id": customer_id,

            "service_id": service_id,

            "title": title,

            "description": description,

            "intent": intent,

            "status": "open",

            "priority": "medium",

            "channel": channel,

            "ticket_type": ticket_type,

            "language": "pt",

            "created_at":
                datetime.utcnow().isoformat()

        }


        result = (
            database
            .table("tickets")
            .insert(ticket)
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



def find_open_ticket(
    customer_id:int,
    intent:str=None,
    service_id=None
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
                "status",
                "open"
            )
            .execute()

        )


        tickets = result.data or []


        for ticket in tickets:


            same_intent = (

                not intent

                or

                ticket.get("intent")
                == intent

            )


            same_service = (

                not service_id

                or

                ticket.get("service_id")
                == service_id

            )


            if same_intent and same_service:

                return ticket



        return None



    except Exception as error:


        print(
            "[FIND TICKET ERROR]",
            error
        )

        return None




def get_ticket(ticket_id:int):

    try:

        result = (

            database
            .table("tickets")
            .select("*")
            .eq(
                "id",
                ticket_id
            )
            .execute()

        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:


        print(
            "[GET TICKET ERROR]",
            error
        )

        return None




def list_tickets():

    try:

        result = (

            database
            .table("tickets")
            .select("*")
            .order(
                "created_at",
                desc=True
            )
            .execute()

        )


        return result.data or []


    except Exception as error:

        print(
            "[LIST TICKETS ERROR]",
            error
        )

        return []




def update_ticket(
    ticket_id:int,
    data:dict
):

    try:

        result = (

            database
            .table("tickets")
            .update(data)
            .eq(
                "id",
                ticket_id
            )
            .execute()

        )


        if result.data:

            return result.data[0]


        return None



    except Exception as error:

        print(
            "[UPDATE TICKET ERROR]",
            error
        )

        return None




def close_ticket(ticket_id:int):

    return update_ticket(
        ticket_id,
        {
            "status":"closed"
        }
    )



def cancel_ticket(ticket_id:int):

    return update_ticket(
        ticket_id,
        {
            "status":"cancelled"
        }
    )



# Compatibility aliases

def crear_ticket(
    cliente_id,
    servicio_id=None,
    descripcion="",
    titulo="Nuevo Ticket"
):

    return create_ticket(

        customer_id=cliente_id,

        service_id=servicio_id,

        description=descripcion,

        title=titulo

    )



def listar_tickets():

    return list_tickets()



def obtener_ticket(ticket_id):

    return get_ticket(ticket_id)



def actualizar_ticket(ticket_id, datos):

    return update_ticket(
        ticket_id,
        datos
    )



def cerrar_ticket(ticket_id):

    return close_ticket(ticket_id)



def cancelar_ticket(ticket_id):

    return cancel_ticket(ticket_id)
def get_open_ticket(
    customer_id: int,
    service_id: int = None,
    intent: str = None
):
    """
    Returns an existing open ticket for a customer.
    Prevents duplicated tickets.
    """

    try:

        query = (
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
        )


        result = query.execute()


        tickets = result.data or []


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
            "[GET OPEN TICKET ERROR]",
            error
        )

        return None