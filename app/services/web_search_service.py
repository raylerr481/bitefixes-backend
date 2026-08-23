"""Compatibility gateway for Bitey's canonical web intelligence engine.

There must be one web-research implementation in Bitey.  Older callers import
``app.services.web_search_service``; this module keeps that API stable while
routing all work through ``app.ai.web_intelligence``.
"""
from __future__ import annotations

from typing import Any, Dict


def search_web(
    query: str,
    language: str = "en",
    limit: int = 8,
    *,
    intent: str | None = None,
    company_id: int | None = None,
) -> Dict[str, Any]:
    """Run governed web research through Bitey's canonical engine.

    ``language`` is retained for compatibility with existing channel callers.
    The canonical engine currently derives search language from its provider
    configuration; preserving this argument avoids breaking those callers.
    """
    from app.ai.web_intelligence import search_web as governed_search_web

    result = governed_search_web(
        query,
        intent=intent,
        limit=limit,
        company_id=company_id,
    )

    # Preserve the legacy response fields expected by existing consumers.
    return {
        "provider": (result.get("providers") or [None])[0],
        "results": result.get("results") or [],
        "fallback_used": bool(
            result.get("providers")
            and result.get("providers")[0] == "tavily"
        ),
        "verified": bool(result.get("verification", {}).get("verified")),
        "verification": result.get("verification") or {},
        "grounding_status": result.get("grounding_status"),
        "memory_hit": bool(result.get("memory_hit")),
        "cache_hit": bool(result.get("cache_hit")),
        "queries": result.get("queries") or [query],
        "context": result.get("context") or "",
    }
