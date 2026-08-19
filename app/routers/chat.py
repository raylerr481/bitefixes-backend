"""Bitey Chat Router V21 - one conversational contract for every channel."""

from fastapi import APIRouter

from app.schemas.chat_schema import ChatRequest
from app.core.bitey import process_message
from app.core.channel_preferences import normalize_contact_channel

router = APIRouter()


@router.post("/chat")
def chat(request: ChatRequest):
    try:
        result = process_message(
            company_id=request.company_id,
            message=request.message,
            phone=request.phone or "",
            customer_name=request.customer_name or "",
            channel=request.channel,
            conversation_id=request.conversation_id,
            language_preference=request.language_preference,
            last_name=request.last_name or "",
            email=request.email or "",
            preferred_contact_channel=normalize_contact_channel(request.preferred_contact_channel),
        )
        return result
    except Exception as error:
        import traceback
        print("[CHAT ERROR]", error)
        traceback.print_exc()
        return {"success": False, "response": "Error procesando solicitud.", "error": str(error)}
