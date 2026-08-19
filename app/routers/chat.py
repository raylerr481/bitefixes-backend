"""Bitey Chat Router V21 - one conversational contract for every channel."""

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
            phone=request.phone or "",
            customer_name=request.customer_name or "Customer",
            channel=request.channel,
            conversation_id=request.conversation_id,
            language_preference=request.language_preference,
        )
        if isinstance(result, dict) and request.preferred_contact_channel:
            result["preferred_contact_channel"] = request.preferred_contact_channel
        return result
    except Exception as error:
        import traceback
        print("[CHAT ERROR]", error)
        traceback.print_exc()
        return {"success": False, "response": "Error procesando solicitud.", "error": str(error)}
