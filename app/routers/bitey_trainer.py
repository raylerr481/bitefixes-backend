"""Bitey Trainer API.

Advisory endpoints for the Bitey IA capability marketed by BiteFixes.
Business actions, payments and external job acceptance remain outside this router.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.bitey_trainer_service import evaluate_responses, build_training_plan, human_task_policy

router = APIRouter(prefix="/bitey-trainer", tags=["bitey-trainer"])


class Candidate(BaseModel):
    provider: str = "unknown"
    response: str = Field(min_length=1)


class EvaluationRequest(BaseModel):
    prompt: str = Field(min_length=1)
    responses: list[Candidate] = Field(min_length=1, max_length=10)


class PlanRequest(BaseModel):
    company: str = "BiteFixes"
    domain: str = "AI"
    service: str = "Bitey Trainer"
    needs: list[str] = []


@router.get("/status")
def status():
    return {"success": True, "service": "Bitey Trainer", "product": "Bitey IA", "commercial_owner": "BiteFixes", "mode": "governed-advisory"}


@router.get("/human-task-policy")
def task_policy():
    return human_task_policy()


@router.post("/evaluate")
def evaluate(request: EvaluationRequest):
    return {"success": True, **evaluate_responses(request.prompt, [item.model_dump() for item in request.responses])}


@router.post("/plan")
def plan(request: PlanRequest):
    return {"success": True, **build_training_plan(company=request.company, domain=request.domain, service=request.service, needs=request.needs)}
