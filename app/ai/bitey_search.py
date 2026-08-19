"""Bitey-owned web search and safe evidence retrieval.

Primary discovery is Bitey's self-hosted SearXNG instance. Tavily is a
secondary fallback only. Brave, Bing and Google providers are blocked.
"""
from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
from typing import Any, Dict, List
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from urllib import robotparser

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
    request = Request("https://api.tavily.com/search", data=payload,
                      headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, method="POST")
    timeout = float(os.getenv("BITEY_SEARCH_TIMEOUT", "8"))
    with urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    return (body.get("results") or []) if isinstance(body, dict) else []


def _public_host(host: str) -> bool:
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
        for address in addresses:
            ip = ipaddress.ip_address(address)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        return bool(addresses)
    except Exception:
        return False


def _clean_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript|svg|template).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def _fetch_evidence(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or not _public_host(parsed.hostname):
        return ""
    try:
        rp = robotparser.RobotFileParser()
        rp.set_url(f"{parsed.scheme}://{parsed.hostname}/robots.txt")
        rp.read()
        if not rp.can_fetch("BiteyWebIntelligence/1.0", url):
            return ""
    except Exception:
        # Failure to read robots.txt is not treated as permission to crawl deeply;
        # the fetch is still bounded and limited to search-result pages.
        pass
    request = Request(url, headers={"Accept": "text/html,text/plain;q=0.9", "User-Agent": "BiteyWebIntelligence/1.0"})
    timeout = float(os.getenv("BITEY_WEB_FETCH_TIMEOUT", "6"))
    max_bytes = int(os.getenv("BITEY_WEB_FETCH_MAX_BYTES", "120000"))
    with urlopen(request, timeout=timeout) as response:
        content_type = (response.headers.get("Content-Type") or "").lower()
        if not ("text/html" in content_type or "text/plain" in content_type):
            return ""
        data = response.read(max_bytes)
    return _clean_html(data.decode("utf-8", errors="ignore"))[:16000]


def _enrich_results(results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    fetch_enabled = os.getenv("BITEY_WEB_FETCH_CONTENT", "true").lower() in {"1", "true", "yes", "on"}
    if not fetch_enabled:
        return results
    fetch_count = max(0, min(int(os.getenv("BITEY_WEB_FETCH_RESULTS", "5")), limit))
    enriched = []
    for index, item in enumerate(results):
        item = dict(item)
        if index < fetch_count:
            try:
                content = _fetch_evidence(str(item.get("url") or ""))
                if content:
                    item["content"] = content
                    item["content_fetched"] = True
            except Exception:
                item["content_fetched"] = False
        enriched.append(item)
    return enriched


def search(query: str, limit: int = 8) -> Dict[str, Any]:
    """Search using Bitey's gateway, then Tavily only as secondary fallback."""
    query = (query or "").strip()
    if not query:
        return {"provider": "unavailable", "results": [], "fallback_used": False}
    try:
        primary = _search_searxng(query, limit)
    except Exception:
        primary = []
    if primary:
        return {"provider": "bitey-searxng", "results": _enrich_results(primary, limit), "fallback_used": False}
    try:
        secondary = _search_tavily(query, limit)
    except Exception:
        secondary = []
    if secondary:
        return {"provider": "tavily", "results": _enrich_results(secondary, limit), "fallback_used": True}
    return {"provider": "unavailable", "results": [], "fallback_used": False}
