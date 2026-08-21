"""Persist provider evaluations and model telemetry in Supabase."""
from __future__ import annotations

from typing import Any

from app.supabase_client import supabase


def _score(answer: str, context: dict[str, Any]) -> dict[str, float]:
    text = (answer or "").lower()
    business = context.get("business_context") or {}
    history = context.get("memory") or {}
    concrete_need = bool(context.get("cognitive_state", {}).get("need"))
    catalog = any(marker in text for marker in ("puedo ayudarte con soporte", "celulares, computadoras", "cámaras, redes"))
    invented = any(marker in text for marker in ("tu técnico", "precio es", "dirección es", "disponible mañana")) and not context.get("verified_evidence")
    return {
        "context": 1.0 if business else 0.7,
        "vocabulary": 1.0 if business and any(str(v).lower() in text for v in (business.get("name"), business.get("business_type"))) else 0.7,
        "service_alignment": 0.9 if concrete_need and not catalog else (0.5 if catalog else 0.75),
        "question": 0.9 if ("?" in answer or "¿" in answer) and concrete_need else 0.7,
        "solution": 0.85 if history or concrete_need else 0.7,
        "factual": 0.4 if invented else 0.9,
        "safety": 1.0 if not invented else 0.4,
        "outcome": 0.8,
    }


def record_provider_evaluation(*, company_id: int, interaction_id: str, provider: str,
                               task_type: str, answer: str, context: dict[str, Any]) -> dict[str, Any] | None:
    scores = _score(answer, context)
    overall = round(sum(scores.values()) / len(scores), 4)
    row = {
        "company_id": company_id,
        "interaction_id": interaction_id,
        "domain": str((context.get("business_context") or {}).get("business_type") or "business"),
        "task_type": task_type,
        "external_provider": provider,
        "context_score": scores["context"],
        "vocabulary_score": scores["vocabulary"],
        "service_alignment_score": scores["service_alignment"],
        "question_score": scores["question"],
        "solution_score": scores["solution"],
        "factual_score": scores["factual"],
        "safety_score": scores["safety"],
        "outcome_score": scores["outcome"],
        "overall_score": overall,
        "evaluator_type": "bitey_governance",
        "evidence": {"scores": scores, "model_answer_length": len(answer or "")},
    }
    try:
        result = supabase.table("bitey_ai_evaluations").insert(row).execute()
        return (result.data or [None])[0]
    except Exception as exc:
        print("[AI EVALUATION WARNING]", type(exc).__name__)
        return None
