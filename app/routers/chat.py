"""Bitey Chat Router - channel-neutral API contract."""

from fastapi import APIRouter

from app.schemas.chat_schema import ChatRequest
from app.services.bitey_gateway import handle_message

router = APIRouter()


@router.post("/chat")
def chat(request: ChatRequest):
    try:
        return handle_message(
            company_id=request.company_id,
            message=request.message,
            phone=request.phone or "",
            email=request.email or "",
            customer_name=request.customer_name or "Customer",
            last_name=request.last_name or "",
            channel=request.channel,
            conversation_id=request.conversation_id,
            language_preference=request.language_preference,
            preferred_contact_channel=request.preferred_contact_channel,
            page_context=request.page_context,
            service_context=request.service_context,
        )
    except Exception as error:
        import traceback
        print("[CHAT ERROR]", error)
        traceback.print_exc()
        return {"success": False, "response": "Error procesando solicitud.", "error": str(error)}
