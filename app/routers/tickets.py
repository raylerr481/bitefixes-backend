"""
BiteFixes Tickets Router V16

HTTP API layer for ticket management.

Responsibilities:
- Receive ticket API requests
- Call ticket_service
- Return JSON responses

Does NOT:
- Create business logic
- Detect intent
- Manage workflows
- Talk directly with Supabase

Architecture:

Client
  |
  v
FastAPI Router
  |
  v
Ticket Service
  |
  v
Supabase
"""

from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException

from app.services.ticket_service import (
    create_ticket,
    process_ticket,
    find_open_ticket,
    update_ticket_language,
    obtener_ticket,
    listar_tickets,
)


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


# =====================================================
# LIST TICKETS
# =====================================================

@router.get("/")
def list_tickets():

    try:

        tickets = listar_tickets()

        return {
            "status": "success",
            "tickets": tickets
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )



# =====================================================
# GET TICKET BY ID
# =====================================================

@router.get("/{ticket_id}")
def get_ticket(ticket_id: int):

    try:

        ticket = obtener_ticket(ticket_id)

        if not ticket:

            raise HTTPException(
                status_code=404,
                detail="Ticket not found"
            )


        return {
            "status": "success",
            "ticket": ticket
        }


    except HTTPException:

        raise


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )



# =====================================================
# CREATE TICKET
# =====================================================

@router.post("/")
def create_ticket_endpoint(
    customer_id: int,
    service_id: Optional[int] = None,
    description: str = "",
    title: str = "Support Request",
    intent: Optional[str] = None,
    company_id: int = 1,
    channel: str = "website",
    language: str = "es"
):

    try:

        ticket = create_ticket(
            customer_id=customer_id,
            service_id=service_id,
            description=description,
            title=title,
            intent=intent,
            company_id=company_id,
            channel=channel,
            language=language
        )


        return {
            "status": "success",
            "ticket": ticket
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )



# =====================================================
# FIND OPEN TICKET
# =====================================================

@router.get("/customer/{customer_id}/open")
def get_open_ticket(
    customer_id: int,
    service_id: Optional[int] = None
):

    try:

        ticket = find_open_ticket(
            customer_id=customer_id,
            service_id=service_id
        )


        return {
            "status": "success",
            "ticket": ticket
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )



# =====================================================
# UPDATE TICKET LANGUAGE
# =====================================================

@router.patch("/{ticket_id}/language")
def change_ticket_language(
    ticket_id: int,
    language: str
):

    try:

        result = update_ticket_language(
            ticket_id=ticket_id,
            language=language
        )


        return {
            "status": "success",
            "ticket": result
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )