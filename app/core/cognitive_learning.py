"""Bitey cognitive learning coordinator.

Training-free learning layer: anchors -> situation -> external AI -> evaluation ->
experience replay -> validated knowledge. It never promotes a fact merely because
an external model suggested it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CognitiveSituation:
    enterprise_anchor: str
    domain_anchor: str | None = None
    area_anchor: str | None = None
    service_anchor: str | None = None
    capability_anchors: list[str] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    signature: str = ""


@dataclass
class LearningPlan:
    situation: CognitiveSituation
    external_ai_roles: list[str]
    checks: list[str]
    learning_models: list[str]
    promotion_rule: str


def build_learning_plan(situation: CognitiveSituation) -> LearningPlan:
    return LearningPlan(
        situation=situation,
        external_ai_roles=["reasoner", "critic", "verifier"],
        checks=[
            "enterprise_context_alignment",
            "service_capability_alignment",
            "evidence_or_outcome_verification",
            "contradiction_check",
        ],
        learning_models=[
            "retrieval_augmented_context",
            "continual_incremental_learning",
            "external_ai_feedback_learning",
            "cognitive_evaluation",
            "knowledge_graph_learning",
            "experience_replay",
            "reflection_and_retry",
            "hindsight_experience_consolidation",
        ],
        promotion_rule="candidate -> validated only after contextual evidence/evaluation; promoted only after repeated support",
    )


def learning_job_types() -> list[str]:
    return ["discover", "evaluate", "replay", "consolidate", "mastery"]


def trigger_sources() -> list[str]:
    return ["schedule", "interaction", "document", "web", "external_ai", "manual"]
