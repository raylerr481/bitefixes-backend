"""
Ticket Service

Handles ticket creation,
search and customer support workflows.
"""

from datetime import datetime

from app.database.supabase import database


# =========================================
# CREATE TICKET
# =========================================

def create_ticket(
    company_id: int,
    customer_id: int,
    title: str,
    description: str,
    intent: str = None,
    service_id: int = None,
    priority: str = "normal"
):

    try:

        ticket_code = (
            f"BF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        data = {

            "company_id": company_id,

            "customer_id": customer_id,

            "title": title,

            "description": description,

            "status": "open",

            "priority": priority,

            "intent": intent,

            "service_id": service_id,

            "ticket_code": ticket_code,

            "codigo_ticket": ticket_code

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


    except Exception as e:

        print(
            "[TICKET CREATE ERROR]",
            e
        )

        return None



# =========================================
# FIND OPEN TICKET
# =========================================

def find_open_ticket(
    customer_id: int,
    intent: str
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
                "intent",
                intent
            )
            .in_(
                "status",
                [
                    "open",
                    "Aberto",
                    "Abierto"
                ]
            )
            .order(
                "created_at",
                desc=True
            )
            .limit(1)
            .execute()
        )


        if result.data:

            return result.data[0]


        return None


    except Exception as e:

        print(
            "[FIND TICKET ERROR]",
            e
        )

        return None