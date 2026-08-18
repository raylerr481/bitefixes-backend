"""Bitey Semantic Source Service V1.

Orchestrates acquisition from external sources without coupling Bitey to a
specific search engine, crawler, LLM, OCR, vision, or transcription vendor.

Adapters provide normalized payloads; this service registers the source,
records the observation, and optionally creates a semantic candidate.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from app.services.semantic_learning_service import register_source, record_observation
from app.services.semantic_intelligence_service import evaluate_candidate, observe_and_propose


ALLOWED_SOURCE_TYPES = {
    "web", "search", "api", "rss", "document", "pdf", "image", "video",
    "audio", "database", "crm", "conversation", "user_feedback", "other",
}


def _validate_source_type(source_type: str) -> str:
    if source_type not in ALLOWED_SOURCE_TYPES:
        raise ValueError(f"Unsupported semantic source type: {source_type}")
    return source_type


def register_external_source(
    source_type: str,
    uri: Optional[str] = None,
    title: Optional[str] = None,
    publisher: Optional[str] = None,
    language: Optional[str] = None,
    authority_score: float = 0.5,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    _validate_source_type(source_type)
    return register_source(
        source_type=source_type,
        uri=uri,
        title=title,
        publisher=publisher,
        language=language,
        authority_score=max(0.0, min(1.0, authority_score)),
        metadata=metadata,
    )


def ingest_normalized_source(
    source: Dict[str, Any],
    modality: str,
    extracted_text: Optional[str] = None,
    extracted_data: Optional[Dict[str, Any]] = None,
    detected_terms: Optional[Iterable[str]] = None,
    confidence: float = 0.5,
    scope: str = "global",
    company_id: Optional[int] = None,
    content_ref: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist normalized content from any acquisition adapter."""
    observation = record_observation(
        modality=modality,
        content_ref=content_ref or source.get("uri"),
        extracted_text=extracted_text,
        extracted_data=extracted_data,
        detected_terms=detected_terms,
        confidence=confidence,
        scope=scope,
        company_id=company_id,
        source_id=source.get("id"),
    )
    return {"source": source, "observation": observation}


def learn_from_external_source(
    source_type: str,
    modality: str,
    proposed_code: str,
    proposed_name: str,
    description: Optional[str] = None,
    uri: Optional[str] = None,
    title: Optional[str] = None,
    publisher: Optional[str] = None,
    language: Optional[str] = None,
    authority_score: float = 0.5,
    extracted_text: Optional[str] = None,
    extracted_data: Optional[Dict[str, Any]] = None,
    detected_terms: Optional[Iterable[str]] = None,
    confidence: float = 0.5,
    scope: str = "global",
    company_id: Optional[int] = None,
    content_ref: Optional[str] = None,
) -> Dict[str, Any]:
    """End-to-end acquisition: source -> observation -> candidate."""
    source = register_external_source(
        source_type=source_type,
        uri=uri,
        title=title,
        publisher=publisher,
        language=language,
        authority_score=authority_score,
    )
    result = observe_and_propose(
        modality=modality,
        proposed_code=proposed_code,
        proposed_name=proposed_name,
        description=description,
        extracted_text=extracted_text,
        extracted_data=extracted_data,
        detected_terms=detected_terms,
        confidence=confidence,
        scope=scope,
        company_id=company_id,
        source_id=source.get("id"),
    )
    return {"source": source, **result}


def evaluate_external_candidate(candidate_id: int) -> Dict[str, Any]:
    return evaluate_candidate(candidate_id)
