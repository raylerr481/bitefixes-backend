"""
Bitey Semantic Learning Service V1
==================================

Controlled semantic acquisition layer for Bitey.

It accepts observations from text, HTML, documents, images, video, audio and
structured data, records evidence, and creates candidates for semantic
expansion. It deliberately does NOT auto-promote untrusted observations into
the global ontology.

Promotion should be performed by a later governance/review layer after
confidence, evidence, source quality and scope rules are evaluated.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Dict, Iterable, Optional

from app.database.supabase import database


SUPPORTED_MODALITIES = {
    "text",
    "html",
    "pdf",
    "image",
    "video",
    "audio",
    "document",
    "structured_data",
}

SUPPORTED_SCOPES = {"global", "industry", "company", "user", "conversation"}


def _validate_scope(scope: str) -> str:
    if scope not in SUPPORTED_SCOPES:
        raise ValueError(f"Unsupported semantic scope: {scope}")
    return scope


def _validate_modality(modality: str) -> str:
    if modality not in SUPPORTED_MODALITIES:
        raise ValueError(f"Unsupported semantic modality: {modality}")
    return modality


def _hash_payload(payload: Any) -> str:
    return sha256(repr(payload).encode("utf-8")).hexdigest()


def register_source(
    source_type: str,
    uri: Optional[str] = None,
    title: Optional[str] = None,
    publisher: Optional[str] = None,
    language: Optional[str] = None,
    authority_score: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    response = database.table("semantic_sources").insert({
        "source_type": source_type,
        "uri": uri,
        "title": title,
        "publisher": publisher,
        "language": language,
        "authority_score": authority_score,
        "metadata": metadata or {},
    }).execute()
    return (response.data or [{}])[0]


def record_observation(
    modality: str,
    content_ref: Optional[str] = None,
    extracted_text: Optional[str] = None,
    extracted_data: Optional[Dict[str, Any]] = None,
    detected_terms: Optional[Iterable[str]] = None,
    confidence: float = 0.5,
    scope: str = "global",
    company_id: Optional[int] = None,
    source_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Store a normalized multimodal observation without promoting knowledge."""
    _validate_modality(modality)
    _validate_scope(scope)

    row = {
        "source_id": source_id,
        "company_id": company_id,
        "scope": scope,
        "modality": modality,
        "content_ref": content_ref,
        "extracted_text": extracted_text,
        "extracted_data": extracted_data or {},
        "detected_terms": list(detected_terms or []),
        "confidence": max(0.0, min(1.0, confidence)),
        "status": "observed",
    }

    response = database.table("semantic_observations").insert(row).execute()
    observation = (response.data or [{}])[0]

    database.table("semantic_learning_events").insert({
        "event_type": "observation_recorded",
        "source_type": modality,
        "source_ref": content_ref,
        "company_id": company_id,
        "scope": scope,
        "input_hash": _hash_payload(row),
        "changes": {"observation_id": observation.get("id")},
        "confidence": row["confidence"],
        "outcome": "observed",
    }).execute()

    return observation


def propose_concept(
    proposed_code: str,
    proposed_name: str,
    description: Optional[str],
    candidate_type: str = "concept",
    confidence: float = 0.5,
    scope: str = "global",
    company_id: Optional[int] = None,
    source_observation_id: Optional[int] = None,
    proposed_relationships: Optional[list] = None,
) -> Dict[str, Any]:
    """Create a candidate semantic concept for validation/governance."""
    _validate_scope(scope)

    response = database.table("semantic_candidates").insert({
        "candidate_type": candidate_type,
        "proposed_code": proposed_code,
        "proposed_name": proposed_name,
        "description": description,
        "scope": scope,
        "company_id": company_id,
        "source_observation_id": source_observation_id,
        "confidence": max(0.0, min(1.0, confidence)),
        "status": "pending",
        "proposed_relationships": proposed_relationships or [],
    }).execute()

    return (response.data or [{}])[0]


def record_evidence(
    observation_id: int,
    concept_id: Optional[int] = None,
    relationship_id: Optional[int] = None,
    evidence_type: str = "supporting",
    excerpt: Optional[str] = None,
    confidence: float = 0.5,
) -> Dict[str, Any]:
    """Attach auditable evidence to a semantic concept or relationship."""
    if concept_id is None and relationship_id is None:
        raise ValueError("Evidence requires a concept_id or relationship_id")

    response = database.table("semantic_evidence").insert({
        "observation_id": observation_id,
        "concept_id": concept_id,
        "relationship_id": relationship_id,
        "evidence_type": evidence_type,
        "excerpt": excerpt,
        "confidence": max(0.0, min(1.0, confidence)),
    }).execute()

    return (response.data or [{}])[0]


def build_learning_candidate(
    observation: Dict[str, Any],
    proposed_code: str,
    proposed_name: str,
    description: Optional[str],
    candidate_type: str = "concept",
    confidence: float = 0.5,
) -> Dict[str, Any]:
    """Convenience pipeline: observation -> candidate, never direct promotion."""
    candidate = propose_concept(
        proposed_code=proposed_code,
        proposed_name=proposed_name,
        description=description,
        candidate_type=candidate_type,
        confidence=confidence,
        scope=observation.get("scope", "global"),
        company_id=observation.get("company_id"),
        source_observation_id=observation.get("id"),
    )

    if observation.get("id") and candidate.get("id"):
        database.table("semantic_learning_events").insert({
            "event_type": "candidate_proposed",
            "source_type": observation.get("modality"),
            "source_ref": observation.get("content_ref"),
            "company_id": observation.get("company_id"),
            "scope": observation.get("scope", "global"),
            "input_hash": _hash_payload(candidate),
            "changes": {"candidate_id": candidate.get("id")},
            "confidence": confidence,
            "outcome": "pending_review",
        }).execute()

    return candidate
