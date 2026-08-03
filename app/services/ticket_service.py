"""
Bitey Ticket Service V10

Responsible for:
- Create tickets
- Generate ticket codes
- Find open tickets
- Update lifecycle
- Multi company support
- Legacy compatibility
"""


from datetime import datetime

from app.database.supabase import database



# =====================================================
# TICKET CODE GENERATOR
# =====================================================

def generate_ticket_code():

    try:

        year = datetime.utcnow().year


        result = (
            database
            .table("tickets")
            .select("id")
            .order(
                "id",
                desc=True
            )
            .limit(1)
            .execute()
        )


        last_id = 0


        if result.data:

            last_id = result.data[0]["id"]


        number = last_id + 1


        return f"BF-{year}-{number:06d}"


    except Exception as error:

        print(
            "[TICKET CODE ERROR]",
            error
        )

        return (
            f"BF-{datetime.utcnow().year}-000001"
        )



# =====================================================
# CREATE TICKET
# =====================================================

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


        code = generate_ticket_code()



        data = {


            "company_id":
                company_id,


            "customer_id":
                customer_id,


            "service_id":
                service_id,


            "title":
                title,


            "description":
                description,


            "intent":
                intent,


            "status":
                "open",


            "priority":
                "medium",


            "channel":
                channel,


            "ticket_type":
                ticket_type,


            "language":
                "pt",


            "ticket_code":
                code,


            "codigo_ticket":
                code,


            "created_at":
                datetime.utcnow().isoformat()

        }



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





# =====================================================
# FIND OPEN TICKET
# =====================================================

def get_open_ticket(
    customer_id:int,
    service_id=None,
    intent=None,
    company_id=None
):

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



        if company_id:

            query = query.eq(
                "company_id",
                company_id
            )



        result = (

            query

            .order(
                "created_at",
                desc=True
            )

            .execute()

        )



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
            "[OPEN TICKET ERROR]",
            error
        )


        return None





# =====================================================
# GET SINGLE TICKET
# =====================================================

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





# =====================================================
# LIST TICKETS
# =====================================================

def list_tickets(
    customer_id=None,
    company_id=None
):

    try:


        query = (

            database

            .table("tickets")

            .select("*")

        )



        if customer_id:

            query = query.eq(
                "customer_id",
                customer_id
            )



        if company_id:

            query = query.eq(
                "company_id",
                company_id
            )



        result = query.execute()



        return result.data or []



    except Exception as error:


        print(
            "[LIST TICKETS ERROR]",
            error
        )


        return []





# =====================================================
# UPDATE TICKET
# =====================================================

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





# =====================================================
# STATUS ACTIONS
# =====================================================

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



def reopen_ticket(ticket_id:int):

    return update_ticket(
        ticket_id,
        {
            "status":"open"
        }
    )



def complete_ticket(ticket_id:int):

    return update_ticket(
        ticket_id,
        {
            "status":"completed"
        }
    )



def assign_ticket(
    ticket_id:int,
    technician_id:int
):

    return update_ticket(
        ticket_id,
        {
            "technician_id": technician_id
        }
    )





# =====================================================
# DELETE
# =====================================================

def delete_ticket(ticket_id:int):

    try:


        result = (

            database

            .table("tickets")

            .delete()

            .eq(
                "id",
                ticket_id
            )

            .execute()

        )


        return result.data



    except Exception as error:


        print(
            "[DELETE TICKET ERROR]",
            error
        )


        return None





# =====================================================
# LEGACY COMPATIBILITY
# Spanish API
# =====================================================

def crear_ticket(*args, **kwargs):

    return create_ticket(
        *args,
        **kwargs
    )



def obtener_ticket(ticket_id):

    return get_ticket(
        ticket_id
    )



def listar_tickets(customer_id=None):

    return list_tickets(
        customer_id
    )



def actualizar_ticket(
    ticket_id,
    datos
):

    return update_ticket(
        ticket_id,
        datos
    )



def cerrar_ticket(ticket_id):

    return close_ticket(
        ticket_id
    )



def cancelar_ticket(ticket_id):

    return cancel_ticket(
        ticket_id
    )



def buscar_ticket_abierto(
    customer_id,
    service_id=None,
    intent=None
):

    return get_open_ticket(
        customer_id,
        service_id,
        intent
    )





# =====================================================
# ENGLISH COMPATIBILITY
# =====================================================

def find_open_ticket(
    customer_id:int,
    intent=None,
    service_id=None
):

    return get_open_ticket(
        customer_id=customer_id,
        service_id=service_id,
        intent=intent
    )



def get_all_tickets(customer_id=None):

    return list_tickets(
        customer_id
    )
# =====================================================
# BITEY V12 PROCESS TICKET
# Central ticket orchestration
# =====================================================

def process_ticket(
    company_id:int,
    customer_id:int,
    service_id=None,
    intent=None,
    description="",
    title="Bitey Request",
    channel="website",
    ticket_type="support",
    create_ticket=True
):

    try:

        # No ticket required
        if not create_ticket:
            return None


        # Check existing ticket

        existing = get_open_ticket(

            customer_id=customer_id,

            service_id=service_id,

            intent=intent,

            company_id=company_id

        )


        if existing:

            print(
                "[EXISTING TICKET]",
                existing.get("ticket_code")
            )

            return existing



        # Create new ticket

        ticket = create_ticket(

            customer_id=customer_id,

            service_id=service_id,

            description=description,

            title=title,

            intent=intent,

            company_id=company_id,

            channel=channel,

            ticket_type=ticket_type

        )


        print(
            "[NEW TICKET]",
            ticket
        )


        return ticket



    except Exception as error:

        print(
            "[PROCESS TICKET ERROR]",
            error
        )

        return None