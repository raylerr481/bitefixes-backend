"""Company intelligence and contextual learning for the external AI council.

External models are used as analysts. They can characterize a company from
trusted source material (website, documents, applications or data extracts),
but they do not write business data directly. This module normalizes their
findings, persists them in Supabase, and builds a company-scoped context for
future Bitey conversations.

Bitey remains the channel-facing apprentice; the external council supplies
current company knowledge until Bitey is mature enough to assume that role.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from app.database.supabase import database

SOURCE_TYPES = {"website", "pdf", "document", "application", "database", "api", "manual"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_source(source: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a company-information source without trusting its content."""
    source_type = str(source.get("source_type") or "manual").lower().strip()
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"unsupported_company_source:{source_type}")
    return {
        "source_type": source_type,
        "uri": str(source.get("uri") or "").strip(),
        "name": str(source.get("name") or "").strip(),
        "content_hash": str(source.get("content_hash") or "").strip(),
        "metadata": source.get("metadata") or {},
    }


def build_company_profile(
    *,
    company_id: int,
    analyses: Iterable[Dict[str, Any]],
    sources: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build a deterministic company profile from independent AI analyses.

    Each analysis should contain the provider name plus structured findings.
    The function does not invent missing company facts.
    """
    analyses = list(analyses)
    normalized_sources = [normalize_source(s) for s in sources]
    providers = sorted({str(a.get("provider")) for a in analyses if a.get("provider")})

    def collect(key: str) -> List[Any]:
        values: List[Any] = []
        for analysis in analyses:
            value = analysis.get(key)
            if isinstance(value, list):
                values.extend(value)
            elif value:
                values.append(value)
        return values

    return {
        "company_id": company_id,
        "company_name": next((a.get("company_name") for a in analyses if a.get("company_name")), None),
        "description": next((a.get("description") for a in analyses if a.get("description")), None),
        "industry": next((a.get("industry") for a in analyses if a.get("industry")), None),
        "services": collect("services"),
        "capabilities": collect("capabilities"),
        "technologies": collect("technologies"),
        "customer_types": collect("customer_types"),
        "business_rules": collect("business_rules"),
        "facts": collect("facts"),
        "sources": normalized_sources,
        "analyst_providers": providers,
        "analysis_count": len(analyses),
        "updated_at": _now(),
    }


def persist_company_profile(profile: Dict[str, Any]) -> Dict[str, Any] | None:
    """Persist the current company intelligence snapshot in Supabase."""
    payload = {
        "company_id": profile["company_id"],
        "company_name": profile.get("company_name"),
        "description": profile.get("description"),
        "industry": profile.get("industry"),
        "profile": profile,
        "updated_at": profile.get("updated_at") or _now(),
    }
    try:
        result = database.table("company_ai_profiles").upsert(payload, on_conflict="company_id").execute()
        return result.data[0] if result.data else payload
    except Exception as error:
        raise RuntimeError(f"company_profile_persist_failed:{error}") from error


def record_company_knowledge(
    *,
    company_id: int,
    records: Iterable[Dict[str, Any]],
    provider: str,
) -> int:
    """Persist granular company facts/services as an auditable knowledge index."""
    rows = []
    for record in records:
        text = str(record.get("content") or record.get("fact") or "").strip()
        if not text:
            continue
        rows.append({
            "company_id": company_id,
            "knowledge_type": str(record.get("knowledge_type") or "fact"),
            "title": str(record.get("title") or "").strip(),
            "content": text,
            "service_key": record.get("service_key"),
            "source_type": record.get("source_type"),
            "source_uri": record.get("source_uri"),
            "provider": provider,
            "confidence": record.get("confidence"),
            "metadata": record.get("metadata") or {},
            "is_active": True,
            "created_at": _now(),
        })
    if not rows:
        return 0
    try:
        result = database.table("company_ai_knowledge").insert(rows).execute()
        return len(result.data or rows)
    except Exception as error:
        raise RuntimeError(f"company_knowledge_persist_failed:{error}") from error


def record_ai_learning_event(*, company_id: int, event: Dict[str, Any]) -> Dict[str, Any] | None:
    """Store what the council learned so Bitey can later learn from outcomes."""
    payload = {
        "company_id": company_id,
        "event_type": event.get("event_type") or "council_observation",
        "input_context": event.get("input_context") or {},
        "provider_outputs": event.get("provider_outputs") or [],
        "decision": event.get("decision") or {},
        "outcome": event.get("outcome") or {},
        "created_at": _now(),
    }
    try:
        result = database.table("ai_learning_events").insert(payload).execute()
        return result.data[0] if result.data else payload
    except Exception as error:
        raise RuntimeError(f"ai_learning_event_persist_failed:{error}") from error


def get_company_context(*, company_id: int, service_key: str | None = None) -> Dict[str, Any]:
    """Load company-specific knowledge for the next Bitey conversation."""
    context: Dict[str, Any] = {"company_id": company_id, "profile": None, "knowledge": []}
    try:
        profile = (
            database.table("company_ai_profiles")
            .select("*")
            .eq("company_id", company_id)
            .limit(1)
            .execute()
        )
        context["profile"] = profile.data[0] if profile.data else None

        query = database.table("company_ai_knowledge").select("*").eq("company_id", company_id).eq("is_active", True)
        if service_key:
            query = query.eq("service_key", service_key)
        knowledge = query.limit(100).execute()
        context["knowledge"] = knowledge.data or []
    except Exception as error:
        raise RuntimeError(f"company_context_load_failed:{error}") from error
    return context


def build_conversation_context(*, company_context: Dict[str, Any], conversation: Dict[str, Any]) -> Dict[str, Any]:
    """Combine company intelligence with the live customer/service context."""
    return {
        "company": company_context.get("profile"),
        "company_knowledge": company_context.get("knowledge", []),
        "customer": conversation.get("customer"),
        "service": conversation.get("service"),
        "message": conversation.get("message"),
        "history": conversation.get("history", []),
        "active_ticket": conversation.get("active_ticket"),
    }
