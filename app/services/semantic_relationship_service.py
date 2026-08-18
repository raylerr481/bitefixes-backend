"""Bitey Semantic Relationship Engine V1.

Builds evidence-backed relationship proposals between semantic concepts.
Promotion remains a separate governance operation.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from app.database.supabase import database

DEFAULT_RELATION_THRESHOLD = 0.85


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def propose_relationship(subject_id: int, predicate: str, object_id: int, confidence: float = 0.5, scope: str = "global", company_id: Optional[int] = None, source_observation_id: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create or reinforce a relationship while preserving provenance."""
    existing = (database.table("semantic_relationships").select("*")
                .eq("subject_id", subject_id).eq("predicate", predicate)
                .eq("object_id", object_id).eq("scope", scope).limit(1).execute())
    values = {
        "subject_id": subject_id, "predicate": predicate, "object_id": object_id,
        "confidence": _clamp(confidence), "evidence_count": 1, "scope": scope,
        "company_id": company_id, "status": "candidate",
        "source_observation_id": source_observation_id, "metadata": metadata or {},
    }
    rows = existing.data or []
    if rows:
        current = rows[0]
        values["confidence"] = max(_clamp(current.get("confidence", 0)), _clamp(confidence))
        values["evidence_count"] = int(current.get("evidence_count", 0)) + 1
        result = database.table("semantic_relationships").update(values).eq("id", current["id"]).execute()
    else:
        result = database.table("semantic_relationships").insert(values).execute()
    return (result.data or [values])[0]


def evaluate_relationship(relationship_id: int) -> Dict[str, Any]:
    """Evaluate a relationship without silently promoting it."""
    result = database.table("semantic_relationships").select("*").eq("id", relationship_id).limit(1).execute()
    relationship = (result.data or [None])[0]
    if not relationship:
        raise ValueError(f"Semantic relationship {relationship_id} not found")
    confidence = _clamp(relationship.get("confidence", 0))
    evidence_count = int(relationship.get("evidence_count", 0))
    ready = confidence >= DEFAULT_RELATION_THRESHOLD and evidence_count >= 2
    changes = {"confidence": confidence, "evidence_count": evidence_count, "ready_for_promotion": ready}
    database.table("semantic_learning_events").insert({
        "event_type": "relationship_evaluated", "source_type": "semantic_relationship",
        "source_ref": str(relationship_id), "company_id": relationship.get("company_id"),
        "scope": relationship.get("scope", "global"), "changes": changes,
        "confidence": confidence, "outcome": "ready_for_promotion" if ready else "pending",
    }).execute()
    return {"relationship": relationship, "evaluation": changes}
