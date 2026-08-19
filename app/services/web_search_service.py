"""Bitey-owned web search gateway.

Primary: Bitey Search Core / self-hosted SearXNG-compatible endpoint.
Secondary: Tavily only. Brave and Brave-like providers are intentionally unsupported.
"""
from __future__ import annotations

from typing import Any, Dict, List
import httpx

from app.config import settings

BLOCKED_PROVIDER_NAMES = {"brave", "bing", "google", "google_search", "brave_search"}


def _normalize_items(items: List[Dict[str, Any]], provider: str) -> List[Dict[str, Any]]:
    if provider.lower() in BLOCKED_PROVIDER_NAMES:
        return []
    normalized = []
    for item in items:
        url = item.get("url") or item.get("link")
        if not url:
            continue
        normalized.append({
            "url": url,
            "title": item.get("title") or "",
            "content": item.get("content") or item.get("snippet") or item.get("description") or "",
            "snippet": item.get("snippet") or item.get("content") or "",
            "published_at": item.get("published_at") or item.get("publishedDate"),
            "source_domain": item.get("source_domain") or item.get("domain"),
            "provider": provider,
        })
    return normalized


def _search_bitey_core(query: str, language: str = "en", limit: int = 8) -> List[Dict[str, Any]]:
    url = getattr(settings, "BITEY_SEARCH_PRIMARY_URL", None) or getattr(settings, "BITEY_WEB_SEARCH_URL", None)
    if not url:
        return []
    try:
        with httpx.Client(timeout=getattr(settings, "BITEY_WEB_SEARCH_TIMEOUT", 8.0)) as client:
            response = client.get(url.rstrip("/") + "/search", params={"q": query, "format": "json", "language": language, "safesearch": 1})
            response.raise_for_status()
            data = response.json()
        return _normalize_items((data.get("results") or [])[:limit], "bitey_search_core")
    except Exception as error:
        print("[BITEY SEARCH WARNING]", error)
        return []


def _search_tavily(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    key = getattr(settings, "TAVILY_API_KEY", None)
    if not key:
        return []
    try:
        with httpx.Client(timeout=getattr(settings, "BITEY_WEB_SEARCH_TIMEOUT", 8.0)) as client:
            response = client.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {key}"},
                json={"query": query, "search_depth": "basic", "max_results": limit, "include_answer": False},
            )
            response.raise_for_status()
            data = response.json()
        return _normalize_items((data.get("results") or [])[:limit], "tavily")
    except Exception as error:
        print("[TAVILY FALLBACK WARNING]", error)
        return []


def search_web(query: str, language: str = "en", limit: int = 8) -> Dict[str, Any]:
    primary = _search_bitey_core(query, language, limit)
    if primary:
        return {"provider": "bitey_search_core", "results": primary, "fallback_used": False}
    secondary = _search_tavily(query, limit)
    if secondary:
        return {"provider": "tavily", "results": secondary, "fallback_used": True}
    return {"provider": None, "results": [], "fallback_used": False}
