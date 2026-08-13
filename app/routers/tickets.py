"""
BiteFixes Tickets Router V17

HTTP API layer.

Responsibilities:

- Receive ticket requests
- Call ticket_service
- Return JSON

Does NOT:

- Create business logic
- Detect intent
- Talk directly with Supabase

Architecture:

Client
 |
 FastAPI Router
 |
 Ticket Service
 |
 Supabase

"""


from typing import Optional

from fastapi import APIRouter, HTTPException


from app.services.ticket_service import (

    create_ticket,

    process_ticket,

    find_open_ticket,

    get_customer_tickets,

    update_ticket_language,

    update_ticket,

    close_ticket,

    obtener_ticket,

    listar_tickets,

)



router = APIRouter(

    prefix="/tickets",

    tags=["Tickets"]

)



# =====================================================
# LIST ALL TICKETS
# =====================================================


@router.get("/")
def list_all_tickets():


    try:


        tickets = listar_tickets()


        return {

            "status":"success",

            "tickets":tickets

        }


    except Exception as error:


        raise HTTPException(

            status_code=500,

            detail=str(error)

        )





# =====================================================
# GET CUSTOMER TICKETS
# =====================================================


@router.get("/customer/{customer_id}")
def customer_tickets(

    customer_id:int,

    company_id:int = 1

):


    try:


        tickets = get_customer_tickets(

            customer_id,

            company_id

        )


        return {

            "status":"success",

            "customer_id":customer_id,

            "tickets":tickets

        }


    except Exception as error:


        raise HTTPException(

            status_code=500,

            detail=str(error)

        )





# =====================================================
# GET OPEN CUSTOMER TICKET
# =====================================================


@router.get("/customer/{customer_id}/open")
def open_customer_ticket(

    customer_id: int,

    intent: str = None,

    company_id: int = 1,

    service_id: int = None,

):

    try:

        ticket = find_open_ticket(
            customer_id=customer_id,
            intent=intent,
            company_id=company_id,
            service_id=service_id,
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
# GET TICKET BY ID
# =====================================================


@router.get("/{ticket_id}")
def get_ticket(

    ticket_id:int

):


    try:


        ticket = obtener_ticket(

            ticket_id

        )


        if not ticket:


            raise HTTPException(

                status_code=404,

                detail="Ticket not found"

            )



        return {


            "status":"success",

            "ticket":ticket


        }



    except HTTPException:


        raise



    except Exception as error:


        raise HTTPException(

            status_code=500,

            detail=str(error)

        )





# =====================================================
# CREATE TICKET MANUAL
# =====================================================


@router.post("/")
def create_ticket_endpoint(

    customer_id:int,

    description:str,

    title:str="Support Request",

    service_id:Optional[int]=None,

    intent:Optional[str]=None,

    company_id:int=1,

    channel:str="website",

    language:str="es",

    ticket_type:str="technical_support"

):


    try:


        ticket = create_ticket(

            customer_id=customer_id,

            company_id=company_id,

            title=title,

            description=description,

            intent=intent,

            service_id=service_id,

            language=language,

            ticket_type=ticket_type,

            channel=channel

        )



        return {


            "status":"success",

            "ticket":ticket


        }




    except Exception as error:


        raise HTTPException(

            status_code=500,

            detail=str(error)

        )





# =====================================================
# UPDATE LANGUAGE
# =====================================================


@router.patch("/{ticket_id}/language")
def change_language(

    ticket_id:int,

    language:str

):


    try:


        result = update_ticket_language(

            ticket_id,

            language

        )


        return {


            "status":"success",

            "ticket":result


        }



    except Exception as error:


        raise HTTPException(

            status_code=500,

            detail=str(error)

        )





# =====================================================
# UPDATE TICKET
# =====================================================


@router.patch("/{ticket_id}")
def edit_ticket(

    ticket_id:int,

    data:dict

):


    try:


        result = update_ticket(

            ticket_id,

            data

        )


        return {


            "status":"success",

            "ticket":result


        }



    except Exception as error:


        raise HTTPException(

            status_code=500,

            detail=str(error)

        )





# =====================================================
# CLOSE TICKET
# =====================================================


@router.post("/{ticket_id}/close")
def close_ticket_endpoint(

    ticket_id:int,

    solution:str=None

):


    try:


        result = close_ticket(

            ticket_id,

            solution

        )


        return {


            "status":"success",

            "ticket":result


        }



    except Exception as error:


        raise HTTPException(

            status_code=500,

            detail=str(error)

        )