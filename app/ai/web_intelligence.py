"""Governed web intelligence for Bitey.

Retrieval is deliberately independent from model providers. The engine adds
bounded query expansion, TTL caching, source authority scoring, corroboration
checks and governed learning candidates. It never promotes web content to
knowledge automatically.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen


CURRENT_MARKERS = {
    "today", "latest", "current", "now", "recent", "price", "prices",
    "version", "release", "update", "news", "2026", "2025", "regulation",
    "law", "licence", "license", "availability", "weather", "stock",
}

_CACHE: Dict[str, tuple[float, Dict[str, Any]]] = {}


@dataclass(frozen=True)
class WebPolicy:
    ttl_seconds: int = int(os.getenv("BITEY_WEB_CACHE_TTL", "900"))
    max_queries: int = int(os.getenv("BITEY_WEB_MAX_QUERIES", "3"))
    max_results: int = int(os.getenv("BITEY_WEB_MAX_RESULTS", "8"))
    verification_min_score: float = float(os.getenv("BITEY_WEB_VERIFY_SCORE", "0.72"))


POLICY = WebPolicy()


def needs_web(message: str, *, intent: Optional[str] = None, knowledge_found: bool = False) -> bool:
    """Decide whether freshness, breadth or a knowledge gap justifies web retrieval."""
    text = (message or "").lower()
    words = set(re.findall(r"[a-z0-9À-ÿ-]+", text))
    if words & CURRENT_MARKERS:
        return True
    if not knowledge_found and len(words) >= 10:
        return True
    if intent in {"research", "comparison", "troubleshooting", "software_update", "product_research"}:
        return True
    return False


def build_queries(message: str, *, intent: Optional[str] = None, max_queries: int | None = None) -> List[str]:
    """Generate a small, diverse query set instead of blindly repeating the prompt."""
    text = re.sub(r"\s+", " ", (message or "").strip())
    if not text:
        return []
    limit = max_queries or POLICY.max_queries
    queries = [text]
    if intent:
        queries.append(f"{intent} {text}")
    lowered = text.lower()
    if any(marker in lowered.split() for marker in ("latest", "current", "today", "version", "update")):
        queries.append(f"{text} official documentation")
    return list(dict.fromkeys(queries))[:limit]


def _domain(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def _domain_score(url: str) -> float:
    host = _domain(url)
    if not host:
        return 0.0
    if host.endswith(".gov") or ".gov." in host:
        return 1.0
    if host.endswith(".edu") or ".edu." in host:
        return 0.95
    if host in {
        "microsoft.com", "support.microsoft.com", "learn.microsoft.com",
        "apple.com", "developer.apple.com", "python.org", "docs.python.org",
        "supabase.com", "render.com", "github.com", "wordpress.com",
    }:
        return 0.98
    if host.startswith("docs."):
        return 0.90
    return 0.55


def _tokenise(text: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9À-ÿ]{3,}", (text or "").lower())
        if token not in {"the", "and", "for", "with", "from", "this", "that", "para", "com", "uma", "que"}
    }


def _normalise_result(item: Dict[str, Any], query: str) -> Optional[Dict[str, Any]]:
    url = str(item.get("url") or item.get("link") or "").strip()
    title = str(item.get("title") or "").strip()
    snippet = str(item.get("snippet") or item.get("content") or item.get("description") or "").strip()
    if not url or not title:
        return None
    relevance_tokens = len(_tokenise(query) & _tokenise(f"{title} {snippet}"))
    relevance = min(1.0, relevance_tokens / max(3, len(_tokenise(query)) * 0.35))
    authority = _domain_score(url)
    score = round((0.55 * relevance) + (0.45 * authority), 3)
    return {
        "url": url,
        "title": title,
        "snippet": snippet[:2500],
        "domain": _domain(url),
        "authority_score": round(authority, 3),
        "relevance_score": round(relevance, 3),
        "score": score,
        "retrieved_at": item.get("retrieved_at") or datetime.now(timezone.utc).isoformat(),
    }


def _deduplicate(results: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    output: List[Dict[str, Any]] = []
    for item in results:
        key = hashlib.sha256((item["url"].rstrip("/") + "|" + item["title"].lower()).encode()).hexdigest()
        if key not in seen:
            seen.add(key)
            output.append(item)
    return output


def _cache_key(message: str, queries: List[str], intent: Optional[str]) -> str:
    raw = json.dumps({"message": message.strip().lower(), "queries": queries, "intent": intent}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str) -> Optional[Dict[str, Any]]:
    entry = _CACHE.get(key)
    if not entry:
        return None
    expires, value = entry
    if expires <= time.time():
        _CACHE.pop(key, None)
        return None
    cached = dict(value)
    cached["cache_hit"] = True
    return cached


def _cache_put(key: str, value: Dict[str, Any]) -> None:
    _CACHE[key] = (time.time() + POLICY.ttl_seconds, dict(value))
    # Keep process-local cache bounded on long-lived Render instances.
    if len(_CACHE) > 256:
        oldest = sorted(_CACHE.items(), key=lambda pair: pair[1][0])[:64]
        for old_key, _ in oldest:
            _CACHE.pop(old_key, None)


def _provider_request(query: str, limit: int) -> List[Dict[str, Any]]:
    """Use Brave directly when configured, otherwise support the generic adapter."""
    brave_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
    if brave_key:
        url = "https://api.search.brave.com/res/v1/web/search"
        params = f"?q={__import__('urllib.parse').parse.quote(query)}&count={max(1, min(20, limit))}"
        request = Request(url + params, headers={
            "Accept": "application/json",
            "X-Subscription-Token": brave_key,
        }, method="GET")
    else:
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
    if brave_key:
        return ((body.get("web") or {}).get("results") or []) if isinstance(body, dict) else []
    if isinstance(body, dict):
        body = body.get("results") or body.get("items") or []
    return body if isinstance(body, list) else []


def _verify(results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
    """Measure corroboration without pretending that search alone proves a fact."""
    domains = {item["domain"] for item in results if item.get("domain")}
    strong = [item for item in results if item.get("score", 0) >= POLICY.verification_min_score]
    token_sets = [_tokenise(f"{item['title']} {item['snippet']}") for item in strong]
    corroborated = False
    if len(token_sets) >= 2:
        common = token_sets[0].copy()
        for token_set in token_sets[1:]:
            common &= token_set
        corroborated = len(common) >= 3
    return {
        "verified": bool(corroborated and len(domains) >= 2 and len(strong) >= 2),
        "corroborated": corroborated,
        "independent_domains": len(domains),
        "strong_sources": len(strong),
        "verification_score": round(min(1.0, (len(strong) / 3) * 0.4 + (len(domains) / 3) * 0.3 + (0.3 if corroborated else 0.0)), 3),
        "note": "corroboration is evidence, not a guarantee of factual correctness",
        "query": query,
    }


def search_web(message: str, *, intent: Optional[str] = None, limit: int | None = None) -> Dict[str, Any]:
    """Retrieve, cache, score and verify evidence; never writes to knowledge."""
    queries = build_queries(message, intent=intent)
    key = _cache_key(message, queries, intent)
    cached = _cache_get(key)
    if cached:
        return cached

    max_results = limit or POLICY.max_results
    raw: List[Dict[str, Any]] = []
    errors: List[str] = []
    for query in queries:
        try:
            raw.extend(_provider_request(query, limit=max(1, max_results // max(1, len(queries)))))
        except Exception as exc:
            errors.append(type(exc).__name__)

    results = [normalised for item in raw if (normalised := _normalise_result(item, message))]
    results = sorted(_deduplicate(results), key=lambda item: item["score"], reverse=True)[:max_results]
    verification = _verify(results, message)
    response = {
        "used": bool(results),
        "queries": queries,
        "results": results,
        "errors": errors,
        "provider": "brave" if os.getenv("BRAVE_SEARCH_API_KEY", "").strip() else "generic",
        "provider_configured": bool(os.getenv("BRAVE_SEARCH_API_KEY", "").strip() or os.getenv("BITEY_WEB_SEARCH_URL", "").strip()),
        "grounding_status": "verified" if verification["verified"] else ("grounded" if results else "unavailable"),
        "verification": verification,
        "cache_hit": False,
        "learning_candidate": bool(verification["verified"] and results),
    }
    _cache_put(key, response)
    return response
