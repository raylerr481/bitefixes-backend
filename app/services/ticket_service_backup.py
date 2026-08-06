"""
BiteFixes Ticket Service V9

Responsibilities:

- Create tickets
- Detect existing tickets
- Avoid duplicates
- Sync language
- Connect services
- Create quotes
- CRM preparation
- Legacy compatibility
"""


from typing import Optional

from app.database.supabase import database

from app.services.quote_service import create_quote



# =====================================================
# FIND OPEN TICKET
# =====================================================


def find_open_ticket(
    customer_id:int,
    service_id:Optional[int]=None,
    intent:Optional[str]=None
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



        if service_id:

            query = query.eq(
                "service_id",
                service_id
            )



        if intent:

            query = query.eq(
                "intent",
                intent
            )



        response = (

            query

            .order(
                "created_at",
                desc=True
            )

            .limit(1)

            .execute()

        )



        if response.data:

            return response.data[0]



        return None



    except Exception as error:


        print(
            "[FIND OPEN TICKET ERROR]",
            error
        )


        return None





# =====================================================
# LEGACY COMPATIBILITY
# =====================================================


def get_open_ticket(
    customer_id,
    intent=None,
    service_id=None
):

    return find_open_ticket(
        customer_id,
        service_id,
        intent
    )





# =====================================================
# UPDATE LANGUAGE
# =====================================================


def update_ticket_language(
    ticket_id:int,
    language:str
):

    try:


        response = (

            database

            .table("tickets")

            .update(
                {
                    "language":language
                }
            )

            .eq(
                "id",
                ticket_id
            )

            .execute()

        )


        return response.data



    except Exception as error:


        print(
            "[UPDATE LANGUAGE ERROR]",
            error
        )


        return None





# =====================================================
# CREATE QUOTE
# =====================================================


def create_ticket_quote(
    ticket,
    title,
    description
):

    try:


        quote = create_quote(

            company_id=ticket.get(
                "company_id",
                1
            ),

            customer_id=ticket["customer_id"],

            service_id=ticket.get(
                "service_id"
            ),

            ticket_id=ticket["id"],

            title=title,

            description=description

        )


        if quote:


            print(
                "[QUOTE CREATED]",
                quote.get(
                    "quote_number"
                )
            )



        return quote



    except Exception as error:


        print(
            "[QUOTE ERROR]",
            error
        )


        return None





# =====================================================
# PROCESS TICKET
# =====================================================


def process_ticket(

    company_id:int,

    customer_id:int,

    service_id:Optional[int],

    intent:Optional[str],

    description:str,

    title:str,

    channel:str,

    language:str,

    ticket_type:str="technical_support",

    create_ticket:bool=False,

    requires_quote:bool=False

):


    if not create_ticket:

        return None





    # ---------------------------------
    # Search duplicate
    # ---------------------------------


    existing = find_open_ticket(

        customer_id,

        service_id,

        intent

    )



    if existing:


        if existing.get(
            "language"
        ) != language:


            update_ticket_language(

                existing["id"],

                language

            )


            existing["language"]=language



        print(

            "[EXISTING TICKET]",

            existing.get(
                "ticket_code"
            )

        )



        return existing





    # ---------------------------------
    # Create ticket
    # ---------------------------------


    try:


        data = {


            "company_id":
                company_id,


            "customer_id":
                customer_id,


            "service_id":
                service_id,


            "intent":
                intent,


            "description":
                description,


            "title":
                title,


            "channel":
                channel,


            "language":
                language,


            "ticket_type":
                ticket_type,


            "status":
                "open",


            "priority":
                "normal"


        }




        response = (

            database

            .table("tickets")

            .insert(data)

            .execute()

        )




        if response.data:


            ticket=response.data[0]



            if requires_quote:


                create_ticket_quote(

                    ticket,

                    title,

                    description

                )



            print(
                "[NEW TICKET]",
                ticket.get(
                    "ticket_code"
                )
            )



            return ticket




        return None




    except Exception as error:


        print(
            "[CREATE TICKET ERROR]",
            error
        )


        return None





# =====================================================
# PUBLIC CREATE
# =====================================================


def create_ticket(

    customer_id,

    service_id=None,

    description="",

    title="Support",

    intent=None,

    company_id=1,

    channel="website",

    language="es",

    ticket_type="technical_support",

    requires_quote=False

):


    return process_ticket(

        company_id,

        customer_id,

        service_id,

        intent,

        description,

        title,

        channel,

        language,

        ticket_type,

        True,

        requires_quote

    )





# =====================================================
# LIST
# =====================================================


def listar_tickets(

    company_id:int=1,

    customer_id:Optional[int]=None

):


    try:


        query=(

            database

            .table("tickets")

            .select("*")

            .eq(
                "company_id",
                company_id
            )

        )



        if customer_id:


            query=query.eq(

                "customer_id",

                customer_id

            )




        response=(

            query

            .order(

                "created_at",

                desc=True

            )

            .execute()

        )



        return response.data or []




    except Exception as error:


        print(
            "[LIST ERROR]",
            error
        )


        return []





# =====================================================
# GET
# =====================================================


def obtener_ticket(ticket_id:int):


    try:


        response=(

            database

            .table("tickets")

            .select("*")

            .eq(
                "id",
                ticket_id
            )

            .execute()

        )


        if response.data:

            return response.data[0]


        return None



    except Exception as error:


        print(
            "[GET TICKET ERROR]",
            error
        )


        return None





# =====================================================
# SPANISH COMPATIBILITY
# =====================================================


def crear_ticket(**kwargs):

    return create_ticket(
        **kwargs
    )