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


# =====================================================
# FIND OPEN TICKET
# =====================================================

def find_open_ticket(
    customer_id: int,
    service_id: Optional[int] = None
):
    """
    Returns the latest open ticket for a customer.
    Optionally filters by service.
    """

    try:

        query = (
            database
            .table("tickets")
            .select("*")
            .eq("customer_id", customer_id)
            .eq("status", "open")
        )

        if service_id is not None:
            query = query.eq("service_id", service_id)

        response = (
            query
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]

        return None

    except Exception as error:

        print("[FIND OPEN TICKET ERROR]", error)
        return None


# =====================================================
# BACKWARD COMPATIBILITY
# =====================================================

def get_open_ticket(
    customer_id,
    intent=None,
    service_id=None
):
    """
    Legacy wrapper used by old workflow modules.

    'intent' is ignored but kept for compatibility.
    """

    return find_open_ticket(
        customer_id=customer_id,
        service_id=service_id
    )


# =====================================================
# UPDATE LANGUAGE
# =====================================================

def update_ticket_language(
    ticket_id: int,
    language: str
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
            .eq("id", ticket_id)
            .execute()
        )

        return response.data

    except Exception as error:

        print("[UPDATE LANGUAGE ERROR]", error)
        return None


# =====================================================
# PROCESS TICKET
# =====================================================

def process_ticket(
    company_id: int,
    customer_id: int,
    service_id: Optional[int],
    intent: Optional[str],
    description: str,
    title: str,
    channel: str,
    language: str,
    ticket_type: str = "technical_support",
    create_ticket: bool = False
):

    if not create_ticket:
        return None

    existing = find_open_ticket(
        customer_id,
        service_id
    )

    if existing:

        if existing.get("language") != language:

            update_ticket_language(
                existing["id"],
                language
            )

            existing["language"] = language

        print("[EXISTING TICKET]", existing.get("ticket_code"))

        return existing

    try:

        data = {

            "company_id": company_id,
            "customer_id": customer_id,
            "service_id": service_id,
            "intent": intent,
            "description": description,
            "title": title,
            "channel": channel,
            "language": language,
            "ticket_type": ticket_type,
            "status": "open",
            "priority": "normal"

        }

        response = (
            database
            .table("tickets")
            .insert(data)
            .execute()
        )

        if response.data:

            ticket = response.data[0]

            print("[NEW TICKET]", ticket)

            return ticket

        return None

    except Exception as error:

        print("[CREATE TICKET ERROR]", error)
        return None


# =====================================================
# LEGACY WRAPPER
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
    """
    Legacy wrapper for old Bitey versions.
    """

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