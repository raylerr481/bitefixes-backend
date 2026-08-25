"""Bitey Trainer: governed evaluation and learning-plan service.

Trainer is a capability of Bitey IA and a billable BiteFixes service. It does
not silently retrain models or promote external-model output to knowledge.
"""
from __future__ import annotations
from hashlib import sha256
from typing import Any

from app.core.cognitive_learning import CognitiveSituation, build_learning_plan


def _score(text: str) -> dict[str, Any]:
    value = str(text or "").strip()
    words = value.split()
    sentences = max(1, sum(value.count(mark) for mark in ".!?"))
    return {
        "length": len(value),
        "word_count": len(words),
        "has_content": bool(value),
        "has_structure": len(words) >= 20 or sentences >= 2,
        "has_uncertainty": any(x in value.lower() for x in ("no sé", "no se", "uncertain", "maybe", "quizá", "tal vez")),
    }


def evaluate_responses(prompt: str, responses: list[dict[str, str]]) -> dict[str, Any]:
    """Evaluate candidate responses using deterministic quality signals only."""
    candidates = []
    for item in responses[:10]:
        text = str(item.get("response") or "")
        metrics = _score(text)
        score = 0.0
        score += 0.35 if metrics["has_content"] else 0.0
        score += 0.25 if metrics["has_structure"] else 0.0
        score += 0.20 if 20 <= metrics["word_count"] <= 500 else 0.10 if metrics["word_count"] else 0.0
        score += 0.20 if not metrics["has_uncertainty"] else 0.0
        candidates.append({"provider": item.get("provider", "unknown"), "score": round(score, 3), "metrics": metrics})
    candidates.sort(key=lambda row: row["score"], reverse=True)
    return {
        "trainer": "bitey-trainer",
        "prompt": str(prompt or "")[:6000],
        "candidates": candidates,
        "best_candidate": candidates[0] if candidates else None,
        "promotion": "advisory_only",
        "note": "Deterministic evaluation is a first-stage signal; no model is automatically retrained or promoted.",
    }


def build_training_plan(*, company: str = "BiteFixes", domain: str = "AI", service: str = "Bitey Trainer", needs: list[str] | None = None) -> dict[str, Any]:
    situation = CognitiveSituation(
        enterprise_anchor=company,
        domain_anchor=domain,
        service_anchor=service,
        needs=list(needs or []),
    )
    situation.signature = sha256(f"{company}|{domain}|{service}|{'|'.join(situation.needs)}".encode()).hexdigest()
    plan = build_learning_plan(situation)
    return {
        "trainer": "bitey-trainer",
        "status": "ready",
        "service": service,
        "situation_signature": situation.signature,
        "roles": plan.external_ai_roles,
        "checks": plan.checks,
        "learning_models": plan.learning_models,
        "promotion_rule": plan.promotion_rule,
    }


def human_task_policy() -> dict[str, Any]:
    return {
        "automatic": ["discover opportunity metadata", "classify task", "prepare instructions", "evaluate permitted outputs"],
        "human_required": ["identity verification", "voice/photo/video capture", "legal acceptance", "payments", "tasks whose platform rules require a human"],
        "approval_required": True,
    }
