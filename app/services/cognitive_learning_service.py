from __future__ import annotations

from hashlib import sha256
from typing import Any

from app.core.cognitive_learning import CognitiveSituation, build_learning_plan


def situation_signature(*parts: str | None) -> str:
    normalized = "|".join((p or "").strip().lower() for p in parts)
    return sha256(normalized.encode("utf-8")).hexdigest()


def build_external_ai_context(*, company_context: dict[str, Any], page_context: dict[str, Any] | None, service_context: dict[str, Any] | None, conversation_context: dict[str, Any] | None, message: str) -> dict[str, Any]:
    page_context = page_context or {}
    service_context = service_context or {}
    conversation_context = conversation_context or {}
    situation = CognitiveSituation(
        enterprise_anchor=str(company_context.get("name") or company_context.get("company") or "unknown"),
        domain_anchor=str(company_context.get("domain") or service_context.get("domain") or ""),
        area_anchor=str(service_context.get("area") or ""),
        service_anchor=str(service_context.get("service") or service_context.get("service_hint") or ""),
        capability_anchors=list(service_context.get("capabilities") or []),
        needs=list(conversation_context.get("needs") or []),
        concepts=list(conversation_context.get("concepts") or []),
    )
    situation.signature = situation_signature(situation.enterprise_anchor, situation.domain_anchor, situation.area_anchor, situation.service_anchor, message)
    plan = build_learning_plan(situation)
    return {
        "enterprise_context_anchor": situation.enterprise_anchor,
        "domain_anchor": situation.domain_anchor,
        "area_anchor": situation.area_anchor,
        "service_anchor": situation.service_anchor,
        "capability_anchors": situation.capability_anchors,
        "needs": situation.needs,
        "concepts": situation.concepts,
        "situation_signature": situation.signature,
        "page_context": page_context,
        "conversation_context": conversation_context,
        "learning_contract": {
            "external_ai_roles": plan.external_ai_roles,
            "checks": plan.checks,
            "models": plan.learning_models,
            "promotion_rule": plan.promotion_rule,
        },
        "message": message,
    }
