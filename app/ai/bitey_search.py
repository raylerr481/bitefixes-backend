"""Bitey-owned web search orchestration.

Primary discovery is a self-hosted SearXNG instance controlled by Bitey.
Tavily is an explicit secondary fallback only. Brave is intentionally
unsupported and blocked at configuration level.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List
from urllib.parse import quote
from urllib.request import Request, urlopen
import json


BLOCKED_PROVIDERS = {"brave", "braveapi", "bing", "google_cse", "google", "brave_search"}


def _provider_name() -> str:
    if os.getenv("BITEY_SEARCH_PRIMARY_URL", "").strip():
        return "bitey-searxng"
    if os.getenv("TAVILY_API_KEY", "").strip():
        return "tavily"
    return "unavailable"


def _assert_allowed(provider: str) -> None:
    if provider.lower().strip() in BLOCKED_PROVIDERS:
        raise RuntimeError("Blocked search provider")


def _search_searxng(query: str, limit: int) -> List[Dict[str, Any]]:
    base = os.getenv("BITEY_SEARCH_PRIMARY_URL", "").strip().rstrip("/")
    if not base:
        return []
    _assert_allowed("bitey-searxng")
    url = f"{base}/search?q={quote(query)}&format=json&language=auto&pageno=1"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "BiteyWebIntelligence/1.0"})
    timeout = float(os.getenv("BITEY_SEARCH_TIMEOUT", "8"))
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return (payload.get("results") or [])[:limit] if isinstance(payload, dict) else []


def _search_tavily(query: str, limit: int) -> List[Dict[str, Any]]:
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key:
        return []
    _assert_allowed("tavily")
    payload = json.dumps({"query": query, "max_results": limit, "search_depth": "basic", "include_answer": False}).encode()
    request = Request(
        "https://api.tavily.com/search",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    timeout = float(os.getenv("BITEY_SEARCH_TIMEOUT", "8"))
    with urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    return (body.get("results") or []) if isinstance(body, dict) else []


def search(query: str, limit: int = 8) -> Dict[str, Any]:
    """Search using Bitey's own gateway, Tavily only as secondary fallback."""
    query = (query or "").strip()
    if not query:
        return {"provider": "unavailable", "results": [], "fallback_used": False}

    try:
        primary = _search_searxng(query, limit)
    except Exception:
        primary = []
    if primary:
        return {"provider": "bitey-searxng", "results": primary, "fallback_used": False}

    try:
        secondary = _search_tavily(query, limit)
    except Exception:
        secondary = []
    return {"provider": "tavily" if secondary else "unavailable", "results": secondary, "fallback_used": bool(secondary)}
