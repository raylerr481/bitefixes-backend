"""Governed web intelligence for Bitey.

Provider-agnostic grounding layer. It deliberately separates retrieval from
model providers so Bitey can switch search vendors without changing Core.
No web result is promoted to knowledge automatically.
"""
from __future__ import annotations

import hashlib
import os
import re
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import json


CURRENT_MARKERS = {
    "today", "latest", "current", "now", "recent", "price", "prices",
    "version", "release", "update", "news", "2026", "2025", "regulation",
    "law", "licence", "license", "availability", "weather", "stock",
}


def needs_web(message: str, *, intent: Optional[str] = None, knowledge_found: bool = False) -> bool:
    """Return True when freshness, breadth, or missing knowledge justifies web retrieval."""
    text = (message or "").lower()
    words = set(re.findall(r"[a-z0-9À-ÿ-]+", text))
    if words & CURRENT_MARKERS:
        return True
    if not knowledge_found and len(words) >= 10:
        return True
    if intent in {"research", "comparison", "troubleshooting", "software_update", "product_research"}:
        return True
    return False


def build_queries(message: str, *, intent: Optional[str] = None, max_queries: int = 3) -> List[str]:
    """Create compact retrieval queries instead of sending raw conversational text."""
    text = re.sub(r"\s+", " ", (message or "").strip())
    if not text:
        return []
    queries = [text]
    if intent:
        queries.append(f"{intent} {text}")
    # A freshness-oriented variant improves retrieval for changing information.
    if any(marker in text.lower().split() for marker in ("latest", "current", "today", "version", "update")):
        queries.append(f"{text} official documentation")
    return list(dict.fromkeys(queries))[:max_queries]


def _domain_score(url: str) -> float:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return 0.0
    if host.endswith(".gov") or ".gov." in host:
        return 1.0
    if host.endswith(".edu") or ".edu." in host:
        return 0.95
    if host in {"microsoft.com", "support.microsoft.com", "apple.com", "developer.apple.com", "python.org", "docs.python.org"}:
        return 0.98
    if host.startswith("docs.") or ".docs." in host:
        return 0.90
    return 0.55


def _normalise_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    url = str(item.get("url") or item.get("link") or "").strip()
    title = str(item.get("title") or "").strip()
    snippet = str(item.get("snippet") or item.get("content") or item.get("description") or "").strip()
    if not url or not title:
        return None
    return {
        "url": url,
        "title": title,
        "snippet": snippet[:2500],
        "source_score": round(_domain_score(url), 3),
        "retrieved_at": item.get("retrieved_at"),
    }


def _deduplicate(results: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    output = []
    for item in results:
        key = hashlib.sha256((item["url"].rstrip("/") + "|" + item["title"].lower()).encode()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _provider_request(query: str, limit: int) -> List[Dict[str, Any]]:
    """Call a configured JSON search adapter. The adapter contract is intentionally tiny."""
    endpoint = os.getenv("BITEY_WEB_SEARCH_URL", "").strip()
    if not endpoint:
        return []
    payload = json.dumps({"query": query, "limit": limit}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = os.getenv("BITEY_WEB_SEARCH_API_KEY", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(endpoint, data=payload, headers=headers, method="POST")
    timeout = float(os.getenv("BITEY_WEB_SEARCH_TIMEOUT", "8"))
    with urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    if isinstance(body, dict):
        body = body.get("results") or body.get("items") or []
    return body if isinstance(body, list) else []


def search_web(message: str, *, intent: Optional[str] = None, limit: int = 8) -> Dict[str, Any]:
    """Retrieve, score and package evidence; never writes to knowledge."""
    queries = build_queries(message, intent=intent)
    raw: List[Dict[str, Any]] = []
    errors: List[str] = []
    for query in queries:
        try:
            raw.extend(_provider_request(query, limit=max(1, limit // max(1, len(queries)))))
        except Exception as exc:
            errors.append(type(exc).__name__)
    results = [r for item in raw if (r := _normalise_result(item))]
    results = sorted(_deduplicate(results), key=lambda x: x["source_score"], reverse=True)[:limit]
    return {
        "used": bool(results),
        "queries": queries,
        "results": results,
        "errors": errors,
        "provider_configured": bool(os.getenv("BITEY_WEB_SEARCH_URL", "").strip()),
        "grounding_status": "grounded" if results else "unavailable",
    }
