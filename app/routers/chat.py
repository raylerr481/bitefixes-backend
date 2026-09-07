"""Bitey Chat Router - channel-neutral API contract."""

from fastapi import APIRouter, HTTPException

from app.schemas.chat_schema import ChatRequest
from app.services.bitey_gateway import handle_message
from app.services.repair_research_service import build_repair_research, tutorial_requested

router = APIRouter()


def _handle(request: ChatRequest, *, enterprise_only: bool = False):
    if enterprise_only and request.product != "bitey-enterprise":
        raise HTTPException(status_code=400, detail="Este canal pertenece a Bitey IA Empresarial de BiteFixes.")
    if enterprise_only and request.context_scope != "bitefixes":
        raise HTTPException(status_code=400, detail="Contexto empresarial inválido para este canal.")

    result = handle_message(
        company_id=request.company_id,
        message=request.message,
        phone=request.phone or "",
        email=request.email or "",
        customer_name=request.customer_name or "Customer",
        last_name=request.last_name or "",
        channel="website" if enterprise_only else request.channel,
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


@router.post("/chat")
def chat(request: ChatRequest):
    """Process a conversation through the central BiteFixes gateway."""
    try:
        return _handle(request)
    except HTTPException:
        raise
    except Exception as error:
        print("[CHAT ERROR]", type(error).__name__)
        raise HTTPException(status_code=500, detail="Error procesando la solicitud.") from error


@router.post("/chat/business")
def business_chat(request: ChatRequest):
    """Dedicated customer-facing channel for Bitey IA Empresarial at BiteFixes.

    This endpoint is intentionally separate from Bitey IA Web. It always runs
    in the BiteFixes tenant, website channel and enterprise context boundary.
    """
    try:
        return _handle(request, enterprise_only=True)
    except HTTPException:
        raise
    except Exception as error:
        print("[BUSINESS CHAT ERROR]", type(error).__name__)
        raise HTTPException(status_code=500, detail="Bitey IA Empresarial no pudo procesar la consulta.") from error
