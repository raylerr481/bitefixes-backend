"""Bitey Chat Router - channel-neutral API contract."""

from fastapi import APIRouter, HTTPException

from app.schemas.chat_schema import ChatRequest
from app.services.bitey_gateway import handle_message
from app.services.repair_research_service import build_repair_research, tutorial_requested

router = APIRouter()


@router.post("/chat")
def chat(request: ChatRequest):
    """Process a Bitey conversation message through the central gateway.

    When the customer explicitly asks for a repair tutorial/video, enrich the
    normal Bitey response with live web and YouTube research derived from the
    active cognitive state. This is intentionally generic and is not tied to a
    particular device or repair type.
    """
    try:
        result = handle_message(
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

        if tutorial_requested(request.message) and isinstance(result, dict):
            research = build_repair_research(
                message=request.message,
                active_problem=result.get("active_problem"),
                active_category=result.get("active_category"),
                active_object=result.get("active_object"),
                active_model=result.get("active_model"),
                language=request.language_preference or "es",
            )
            result["repair_research"] = research

        return result
    except Exception as error:
        # Keep internal exception details out of the public API response.
        print("[CHAT ERROR]", type(error).__name__)
        raise HTTPException(
            status_code=500,
            detail="Error procesando la solicitud.",
        ) from error
