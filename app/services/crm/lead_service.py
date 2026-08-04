"""
=====================================================
BiteFixes Lead Service V16
=====================================================

Responsibilities

- Automatic lead creation
- Avoid duplicate leads
- Connect customers
- Connect tickets
- Prepare sales CRM

=====================================================
"""

from typing import Optional

from app.database.supabase import database


def find_lead(
    customer_id: int
):
    """
    Returns an existing lead.
    """

    try:

        response = (
            database
            .table("crm_leads")
            .select("*")
            .eq("customer_id", customer_id)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]

        return None

    except Exception as error:

        print("[LEAD SEARCH ERROR]", error)

        return None


def create_lead(
    customer_id: int,
    ticket_id: Optional[int],
    service_id: Optional[int],
    intent: Optional[str]
):
    """
    Creates a CRM lead.
    """

    existing = find_lead(customer_id)

    if existing:

        print("[LEAD EXISTS]", existing["id"])

        return existing

    try:

        data = {

            "customer_id": customer_id,

            "ticket_id": ticket_id,

            "service_id": service_id,

            "intent": intent,

            "status": "new"

        }

        response = (

            database
            .table("crm_leads")
            .insert(data)
            .execute()

        )

        if response.data:

            print("[LEAD CREATED]")

            return response.data[0]

        return None

    except Exception as error:

        print("[LEAD CREATE ERROR]", error)

        return None


def update_lead_status(
    lead_id: int,
    status: str
):
    """
    Updates lead status.
    """

    try:

        response = (

            database
            .table("crm_leads")
            .update(
                {
                    "status": status
                }
            )
            .eq(
                "id",
                lead_id
            )
            .execute()

        )

        if response.data:

            print("[LEAD UPDATED]")

            return response.data[0]

        return None

    except Exception as error:

        print("[LEAD UPDATE ERROR]", error)

        return None


def convert_lead(
    customer_id: int
):
    """
    Converts a lead into a customer.
    """

    lead = find_lead(customer_id)

    if not lead:

        return None

    return update_lead_status(

        lead["id"],

        "converted"

    )


def process_lead(
    customer_id: int,
    ticket: Optional[dict],
    service: Optional[dict],
    intent: Optional[str]
):
    """
    Main CRM Lead controller.
    """

    ticket_id = None
    service_id = None

    if ticket:

        ticket_id = ticket.get("id")

    if service:

        service_id = service.get("id")

    return create_lead(

        customer_id=customer_id,

        ticket_id=ticket_id,

        service_id=service_id,

        intent=intent

    )