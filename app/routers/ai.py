"""Controlled Bitey AI diagnostics.

This endpoint is advisory only and never executes business actions.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.runtime import build_ai_orchestrator

router = APIRouter(prefix="/ai", tags=["ai"])


class AIAnalyzeRequest(BaseModel):
    message: str
    language: str | None = None
    context: dict = {}


@router.get("/status")
def ai_status():
    orchestrator = build_ai_orchestrator()
    return {"success": True, "providers": orchestrator.registry.snapshot()}


@router.post("/analyze")
async def ai_analyze(request: AIAnalyzeRequest):
    orchestrator = build_ai_orchestrator()
    result = await orchestrator.ask(
        "Analyze the user's request. Identify likely intent, need, relevant entities, missing information, and confidence. Do not execute actions.",
        capability="semantic_analysis",
        context={"message": request.message, "language": request.language, **request.context},
    )
    return {"success": True, "advisory": result}
