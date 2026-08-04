"""
BiteFixes Ticket Service V15

Responsible for:
- Find existing open tickets
- Create tickets
- Reuse tickets
- Multilingual support
- Workflow compatibility

Database:
tickets
"""

from datetime import datetime

from app.database.supabase import database


# =====================================================
# FIND OPEN TICKET
# =====================================================

def find_open_ticket(
    company_id: int,
    customer_id: int,
    intent: str = None
):

    try:

        query = (
            database
            .table("tickets")
            .select("*")
            .eq(
                "company_id",
                company_id
            )
            .eq(
                "customer_id",
                customer_id
            )
            .eq(
                "status",
                "open"
            )
        )


        if intent:

            query = query.eq(
                "intent",
                intent
            )


        result = (
            query
            .order(
                "created_at",
                desc=True
            )
            .limit(1)
            .execute()
        )


        if result.data:

            ticket = result.data[0]


            print(
                "[EXISTING TICKET]",
                ticket.get(
                    "ticket_code"
                )
                or
                ticket.get(
                    "codigo_ticket"
                )
            )


            return ticket


        return None



    except Exception as error:

        print(
            "[FIND OPEN TICKET ERROR]",
            error
        )

        return None



# =====================================================
# GENERATE TICKET CODE
# =====================================================

def generate_ticket_code(
    ticket_id: int
):

    year = datetime.utcnow().year


    return (
        f"BF-{year}-{ticket_id:06d}"
    )



# =====================================================
# CREATE TICKET
# =====================================================

def create_ticket(
    company_id: int,
    customer_id: int,
    service_id: int,
    intent: str,
    description: str,
    title: str,
    channel: str = "website",
    ticket_type: str = "technical_support",
    language: str = "pt"
):

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


            "status":
                "open",


            "ticket_type":
                ticket_type,


            "channel":
                channel,


            "language":
                language,


            "created_at":
                datetime.utcnow().isoformat()

        }



        result = (

            database
            .table("tickets")
            .insert(data)
            .execute()

        )


        if not result.data:

            return None



        ticket = result.data[0]


        ticket_id = ticket["id"]



        code = generate_ticket_code(
            ticket_id
        )



        database.table(
            "tickets"
        ).update(

            {
                "ticket_code": code
            }

        ).eq(

            "id",
            ticket_id

        ).execute()



        ticket["ticket_code"] = code



        print(
            "[NEW TICKET]",
            code
        )


        return ticket



    except Exception as error:


        print(
            "[CREATE TICKET ERROR]",
            error
        )


        return None



# =====================================================
# PROCESS TICKET
# =====================================================

def process_ticket(
    company_id: int,
    customer_id: int,
    service_id: int,
    intent: str,
    description: str,
    title: str,
    channel: str = "website",
    ticket_type: str = "technical_support",
    create_ticket: bool = True,
    language: str = "pt"
):


    if not create_ticket:

        return None



    existing = find_open_ticket(

        company_id,

        customer_id,

        intent

    )


    if existing:

        return existing



    return create_ticket(

        company_id,

        customer_id,

        service_id,

        intent,

        description,

        title,

        channel,

        ticket_type,

        language

    )



# =====================================================
# COMPATIBILITY
# =====================================================

def get_open_ticket(
    company_id,
    customer_id,
    intent=None
):

    return find_open_ticket(

        company_id,

        customer_id,

        intent

    )