"""Bitey Autonomous Research Engine V1.

Turns a knowledge gap into bounded research tasks. The engine is provider-
agnostic: discovery/fetch/extraction adapters can be attached later without
changing semantic memory. It never treats fetched content as trusted knowledge
by default.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from app.services.semantic_source_service import register_external_source, ingest_normalized_source

DEFAULT_MAX_SOURCES = 5
DEFAULT_MAX_DEPTH = 2
DEFAULT_CONFIDENCE_TARGET = 0.85


def plan_research(
    question: str,
    knowledge_gaps: Iterable[str],
    max_sources: int = DEFAULT_MAX_SOURCES,
    max_depth: int = DEFAULT_MAX_DEPTH,
    confidence_target: float = DEFAULT_CONFIDENCE_TARGET,
) -> Dict[str, Any]:
    """Create a bounded, auditable research plan."""
    gaps = [g.strip() for g in knowledge_gaps if g and g.strip()]
    return {
        "research_id": str(uuid4()),
        "question": question.strip(),
        "gaps": gaps,
        "max_sources": max(1, min(max_sources, 50)),
        "max_depth": max(0, min(max_depth, 5)),
        "confidence_target": max(0.0, min(confidence_target, 1.0)),
        "status": "planned",
        "queries": [g for g in gaps],
    }


def prioritize_sources(
    sources: Iterable[Dict[str, Any]],
    authority_weight: float = 0.55,
    relevance_weight: float = 0.45,
) -> List[Dict[str, Any]]:
    """Rank discovered sources without claiming their content is true."""
    ranked = []
    for source in sources:
        authority = max(0.0, min(1.0, float(source.get("authority_score", 0.5))))
        relevance = max(0.0, min(1.0, float(source.get("relevance_score", 0.5))))
        item = dict(source)
        item["research_score"] = authority * authority_weight + relevance * relevance_weight
        ranked.append(item)
    return sorted(ranked, key=lambda x: x["research_score"], reverse=True)


def register_discovered_sources(
    discovered_sources: Iterable[Dict[str, Any]],
    max_sources: int = DEFAULT_MAX_SOURCES,
) -> List[Dict[str, Any]]:
    """Register only the bounded set selected by the research planner."""
    ranked = prioritize_sources(discovered_sources)
    registered = []
    for source in ranked[:max(1, max_sources)]:
        registered.append(register_external_source(
            source_type=source.get("source_type", "web"),
            uri=source.get("uri"),
            title=source.get("title"),
            publisher=source.get("publisher"),
            language=source.get("language"),
            authority_score=source.get("authority_score", 0.5),
            metadata={"research_score": source.get("research_score", 0.0), "research_id": source.get("research_id")},
        ))
    return registered


def ingest_research_result(
    source: Dict[str, Any],
    modality: str,
    extracted_text: Optional[str],
    extracted_data: Optional[Dict[str, Any]] = None,
    detected_terms: Optional[Iterable[str]] = None,
    confidence: float = 0.5,
    scope: str = "global",
    company_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Store a research result as evidence-bearing observation, not truth."""
    return ingest_normalized_source(
        source=source,
        modality=modality,
        extracted_text=extracted_text,
        extracted_data=extracted_data,
        detected_terms=detected_terms,
        confidence=confidence,
        scope=scope,
        company_id=company_id,
        content_ref=source.get("uri"),
    )


def should_continue_research(
    confidence: float,
    sources_used: int,
    max_sources: int = DEFAULT_MAX_SOURCES,
    target: float = DEFAULT_CONFIDENCE_TARGET,
) -> bool:
    """Stop when the target is met or the bounded source budget is exhausted."""
    return confidence < target and sources_used < max_sources
