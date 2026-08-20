"""Bitey Chat Router - channel-neutral API contract."""

from fastapi import APIRouter, HTTPException

from app.schemas.chat_schema import ChatRequest
from app.services.bitey_gateway import handle_message

router = APIRouter()


@router.post("/chat")
def chat(request: ChatRequest):
    """Process a Bitey conversation message through the central gateway."""
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
        )
    except Exception as error:
        # Keep internal exception details out of the public API response.
        print("[CHAT ERROR]", type(error).__name__)
        raise HTTPException(
            status_code=500,
            detail="Error procesando la solicitud.",
        ) from error
