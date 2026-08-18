"""Bitey Chat Router V18."""

from fastapi import APIRouter

from app.schemas.chat_schema import ChatRequest
from app.core.bitey import process_message

router = APIRouter()


@router.post("/chat")
def chat(request: ChatRequest):
    try:
        result = process_message(
            company_id=request.company_id,
            message=request.message,
            phone=request.phone,
            customer_name=request.customer_name,
            channel=request.channel,
            conversation_id=request.conversation_id,
            language_preference=request.language_preference,
        )
        return result
    except Exception as error:
        import traceback

        print("[CHAT ERROR]", error)
        traceback.print_exc()
        return {
            "success": False,
            "response": "Error procesando solicitud.",
            "error": str(error),
        }
