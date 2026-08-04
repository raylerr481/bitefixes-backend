"""
Bitey Chat Router

API endpoint for:
- Website
- WhatsApp
- Mobile App
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.bitey import process_message


router = APIRouter(
    prefix="/chat",
    tags=["Bitey Chat"]
)


class ChatRequest(BaseModel):

    company_id: int = 1

    customer_id: int | None = None

    message: str

    phone: str

    name: str | None = "Customer"

    channel: str = "website"



class ChatResponse(BaseModel):

    customer_id: int | None = None

    conversation_id: int | None = None

    response: str = ""

    intent: str | None = None

    confidence: int = 0

    workflow: str | None = None

    service: dict | None = None

    ticket_id: int | None = None

    lead_id: int | None = None

    lead: dict | None = None

    channel: str = "website"



@router.post(
    "",
    response_model=ChatResponse
)
def chat(data: ChatRequest):

    try:

        print("==============================")
        print("INCOMING CHAT")
        print(data)
        print("==============================")


        result = process_message(

            company_id=data.company_id,

            message=data.message,

            whatsapp=data.phone,

            customer_name=data.name,

            channel=data.channel

        )


        print("==============================")
        print("BITEY RAW RESULT")
        print(result)
        print("==============================")


        if "error" in result:

            raise Exception(
                result["error"]
            )


        return {

            "customer_id": result.get(
                "customer_id"
            ),

            "conversation_id": result.get(
                "conversation_id"
            ),

            "response": result.get(
                "response",
                ""
            ),

            "intent": result.get(
                "intent"
            ),

            "confidence": result.get(
                "confidence",
                0
            ),

            "workflow": result.get(
                "workflow"
            ),

            "service": result.get(
                "service"
            ),

            "ticket_id": result.get(
                "ticket_id"
            ),

            "lead_id": result.get(
                "lead_id"
            ),

            "lead": result.get(
                "lead"
            ),

            "channel": data.channel

        }


    except Exception as error:

        import traceback

        print("==============================")
        print("CHAT ERROR")
        print(error)

        traceback.print_exc()

        print("==============================")


        raise HTTPException(

            status_code=500,

            detail=str(error)

        )