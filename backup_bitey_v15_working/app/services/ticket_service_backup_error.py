"""
BiteFixes Ticket Service V8

Responsibilities:
- Create tickets
- Detect existing open tickets
- Avoid duplicates
- Sync customer language
- Connect services
- Prepare CRM workflow
"""

from typing import Optional

from app.database.supabase import database


def find_open_ticket(
    customer_id: int,
    service_id: Optional[int] = None
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
            "[FIND TICKET ERROR]",
            error
        )

        return None



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
                    "language": language
                }
            )
            .eq(
                "id",
                ticket_id
            )
            .execute()

        )


        print(
            "[TICKET LANGUAGE UPDATED]",
            response.data
        )


        return response.data


    except Exception as error:

        print(
            "[UPDATE LANGUAGE ERROR]",
            error
        )

        return None



def process_ticket(
    company_id:int,
    customer_id:int,
    service_id:int,
    intent:str,
    description:str,
    title:str,
    channel:str,
    language:str,
    ticket_type:str="technical_support",
    create_ticket:bool=False
):


    if not create_ticket:

        return None



    existing = find_open_ticket(
        customer_id,
        service_id
    )


    if existing:


        print(
            "[EXISTING TICKET]",
            existing.get(
                "ticket_code"
            )
        )


        if existing.get(
            "language"
        ) != language:


            update_ticket_language(
                existing["id"],
                language
            )


            existing["language"] = language



        return existing



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


            ticket = response.data[0]


            print(
                "[NEW TICKET]",
                ticket
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
# COMPATIBILITY WRAPPER
# Bitey V15 legacy support
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
    ticket_type="technical_support"
):

    return process_ticket(

        company_id=company_id,

        customer_id=customer_id,

        service_id=service_id,

        intent=intent,

        description=description,

        title=title,

        channel=channel,

        language=language,

        ticket_type=ticket_type,

        create_ticket=True

    )