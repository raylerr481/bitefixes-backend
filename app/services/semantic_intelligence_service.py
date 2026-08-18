"""Bitey Semantic Intelligence Service V1.

Evidence-driven semantic evolution layer. Acquisition adapters may provide
text, HTML, PDF, image, video, audio or structured-data observations. This
module scores candidates but never silently promotes untrusted knowledge.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from app.database.supabase import database
from app.services.semantic_learning_service import build_learning_candidate, record_observation

DEFAULT_PROMOTION_THRESHOLD = 0.85
DEFAULT_MIN_EVIDENCE = 2


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def score_candidate(candidate: Dict[str, Any], evidence: Iterable[Dict[str, Any]], source_quality: float = 0.5) -> Dict[str, Any]:
    """Score using candidate confidence, independent evidence and source quality."""
    rows = list(evidence)
    evidence_confidence = (
        sum(_clamp(row.get("confidence", 0.0)) for row in rows) / len(rows)
        if rows else 0.0
    )
    score = _clamp(
        _clamp(candidate.get("confidence", 0.0)) * 0.35
        + evidence_confidence * 0.45
        + _clamp(source_quality) * 0.20
    )
    return {
        "score": score,
        "evidence_count": len(rows),
        "ready_for_promotion": len(rows) >= DEFAULT_MIN_EVIDENCE and score >= DEFAULT_PROMOTION_THRESHOLD,
    }


def evaluate_candidate(candidate_id: int) -> Dict[str, Any]:
    """Evaluate a candidate and record an auditable result; never promote it."""
    response = database.table("semantic_candidates").select("*").eq("id", candidate_id).limit(1).execute()
    candidate = (response.data or [None])[0]
    if not candidate:
        raise ValueError(f"Semantic candidate {candidate_id} not found")

    observation_id = candidate.get("source_observation_id")
    evidence = []
    source_quality = 0.5
    if observation_id:
        evidence = database.table("semantic_evidence").select("*").eq("observation_id", observation_id).execute().data or []
        observation = database.table("semantic_observations").select("source_id").eq("id", observation_id).limit(1).execute().data or []
        source_id = observation[0].get("source_id") if observation else None
        if source_id:
            source = database.table("semantic_sources").select("authority_score").eq("id", source_id).limit(1).execute().data or []
            if source:
                source_quality = _clamp(source[0].get("authority_score", 0.5))

    evaluation = score_candidate(candidate, evidence, source_quality)
    database.table("semantic_learning_events").insert({
        "event_type": "candidate_evaluated",
        "source_type": "semantic",
        "source_ref": str(candidate_id),
        "company_id": candidate.get("company_id"),
        "scope": candidate.get("scope", "global"),
        "changes": evaluation,
        "confidence": evaluation["score"],
        "outcome": "ready_for_promotion" if evaluation["ready_for_promotion"] else "pending",
    }).execute()
    return {"candidate": candidate, "evaluation": evaluation}


def observe_and_propose(
    modality: str,
    proposed_code: str,
    proposed_name: str,
    description: Optional[str] = None,
    extracted_text: Optional[str] = None,
    scope: str = "global",
    company_id: Optional[int] = None,
    source_id: Optional[int] = None,
    confidence: float = 0.5,
    detected_terms: Optional[Iterable[str]] = None,
    extracted_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Normalize an observation and create a governed semantic candidate."""
    observation = record_observation(
        modality=modality,
        extracted_text=extracted_text,
        extracted_data=extracted_data,
        detected_terms=detected_terms,
        confidence=confidence,
        scope=scope,
        company_id=company_id,
        source_id=source_id,
    )
    candidate = build_learning_candidate(
        observation=observation,
        proposed_code=proposed_code,
        proposed_name=proposed_name,
        description=description,
        confidence=confidence,
    )
    return {"observation": observation, "candidate": candidate}
