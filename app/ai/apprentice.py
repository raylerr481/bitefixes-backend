"""Bitey apprenticeship layer.

Bitey is deliberately treated as an apprentice while external AI providers
perform cognitive work. Providers can teach, challenge and evaluate Bitey's
proposed decisions, but they never receive direct authority over business
writes. This module produces deterministic learning/evaluation metadata that
can later be persisted by the existing memory/telemetry layers.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List


ROLE_MAP = {
    "groq": "director",
    "deepseek-free": "specialist",
    "qwen-free": "reviewer",
}

CAPABILITY_WEIGHTS = {
    "context_use": 0.20,
    "source_alignment": 0.20,
    "problem_understanding": 0.20,
    "action_quality": 0.20,
    "verification": 0.20,
}


def provider_role(provider: str) -> str:
    return ROLE_MAP.get(provider, "advisor")


def build_learning_context(
    *,
    user_message: str,
    website_context: Dict[str, Any] | None = None,
    backend_context: Dict[str, Any] | None = None,
    conversation_context: Iterable[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Build the shared, read-only context presented to external AI workers."""
    return {
        "learning_mode": "apprentice",
        "bitey_status": "student",
        "user_message": user_message,
        "sources": {
            "website": website_context or {},
            "bitefixes_backend": backend_context or {},
            "conversation": list(conversation_context or []),
        },
        "write_policy": "providers_propose_bitey_validates",
    }


def evaluate_bitey(
    *,
    capability_scores: Dict[str, float],
    minimum_score: float = 0.80,
    minimum_capabilities: int = 4,
) -> Dict[str, Any]:
    """Evaluate whether Bitey may graduate a capability.

    Graduation is deliberately conservative: a capability must meet the
    threshold and enough independent dimensions must have been demonstrated.
    The result is a recommendation only; it does not grant permissions.
    """
    normalized = {
        name: max(0.0, min(1.0, float(value)))
        for name, value in capability_scores.items()
    }
    weighted = sum(
        normalized.get(name, 0.0) * weight
        for name, weight in CAPABILITY_WEIGHTS.items()
    )
    qualified = sum(1 for value in normalized.values() if value >= minimum_score)
    ready = weighted >= minimum_score and qualified >= minimum_capabilities
    return {
        "status": "ready" if ready else "training",
        "weighted_score": round(weighted, 4),
        "qualified_capabilities": qualified,
        "minimum_score": minimum_score,
        "recommendation": "candidate_for_graduation" if ready else "continue_training",
        "scores": normalized,
        "authority_granted": False,
    }


def build_training_record(
    *,
    user_message: str,
    provider_results: List[Dict[str, Any]],
    selected: Dict[str, Any] | None,
    evaluation: Dict[str, Any],
) -> Dict[str, Any]:
    """Create an auditable learning record without writing to the database."""
    return {
        "mode": "apprentice",
        "user_message": user_message,
        "providers": [
            {
                "provider": item.get("provider"),
                "role": provider_role(str(item.get("provider", ""))),
                "status": item.get("status"),
            }
            for item in provider_results
        ],
        "selected_provider": (selected or {}).get("provider"),
        "evaluation": evaluation,
        "next_step": "persist_after_core_validation",
    }
