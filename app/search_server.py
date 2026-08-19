"""Standalone Bitey Search Core HTTP service.

This is Bitey's own search gateway. It does not use Brave, Bing, Google CSE,
or any Brave-compatible API. It performs bounded discovery against allowed
public sources, normalises and ranks results, and exposes a small JSON API.
Tavily remains outside this service as the secondary fallback in the backend.
"""
from __future__ import annotations

import html
import re
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen

from fastapi import FastAPI, Query

app = FastAPI(title="Bitey Search Core", version="1.0.0")

ALLOWED_SOURCES = ("duckduckgo", "wikipedia")
BLOCKED_TERMS = ("brave", "bing", "google")


def _safe_url(url: str) -> bool:
    low = url.lower()
    return not any(term in low for term in BLOCKED_TERMS)


def _duckduckgo(query: str, limit: int) -> list[dict]:
    url = "https://html.duckduckgo.com/html/?q=" + quote(query)
    request = Request(url, headers={"User-Agent": "BiteySearchCore/1.0"})
    with urlopen(request, timeout=8) as response:
        body = response.read().decode("utf-8", errors="ignore")
    results = []
    blocks = re.findall(r'<div class="result__body".*?</div>\s*</div>', body, flags=re.S)
    for block in blocks[:limit * 2]:
        match = re.search(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, flags=re.S)
        if not match:
            continue
        raw_url = html.unescape(match.group(1))
        title = re.sub(r"<.*?>", "", html.unescape(match.group(2))).strip()
        redirect = re.search(r"uddg=([^&]+)", raw_url)
        target = unquote(redirect.group(1)) if redirect else raw_url
        snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</a>|class="result__snippet"[^>]*>(.*?)</div>', block, flags=re.S)
        snippet = "".join(snippet_match.groups()) if snippet_match else ""
        snippet = re.sub(r"<.*?>", "", html.unescape(snippet)).strip()
        if target.startswith("http") and _safe_url(target) and title:
            results.append({"url": target, "title": title, "snippet": snippet, "source": "duckduckgo"})
        if len(results) >= limit:
            break
    return results


def _wikipedia(query: str, limit: int) -> list[dict]:
    url = "https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit=" + str(min(limit, 5)) + "&srsearch=" + quote(query)
    request = Request(url, headers={"User-Agent": "BiteySearchCore/1.0"})
    with urlopen(request, timeout=8) as response:
        data = __import__("json").loads(response.read().decode("utf-8"))
    results = []
    for item in ((data.get("query") or {}).get("search") or []):
        title = item.get("title", "")
        snippet = re.sub(r"<.*?>", "", item.get("snippet", ""))
        if title:
            results.append({"url": "https://en.wikipedia.org/wiki/" + quote(title.replace(" ", "_")), "title": title, "snippet": snippet, "source": "wikipedia"})
    return results


def _score(item: dict, query: str) -> float:
    q = set(re.findall(r"[a-z0-9À-ÿ]{3,}", query.lower()))
    t = set(re.findall(r"[a-z0-9À-ÿ]{3,}", (item.get("title", "") + " " + item.get("snippet", "")).lower()))
    relevance = len(q & t) / max(1, len(q))
    authority = 0.92 if item.get("source") == "wikipedia" else 0.60
    return round(min(1.0, 0.65 * relevance + 0.35 * authority), 3)


@app.get("/")
def health():
    return {"service": "Bitey Search Core", "status": "ok", "providers": list(ALLOWED_SOURCES), "blocked": list(BLOCKED_TERMS)}


@app.get("/search")
def search(query: str = Query(..., min_length=2), limit: int = Query(8, ge=1, le=20)):
    results: list[dict] = []
    errors: list[str] = []
    for source in ALLOWED_SOURCES:
        try:
            found = _duckduckgo(query, limit) if source == "duckduckgo" else _wikipedia(query, min(5, limit))
            results.extend(found)
        except Exception as exc:
            errors.append(f"{source}:{type(exc).__name__}")
    unique = {}
    for item in results:
        unique[item["url"].rstrip("/")] = item
    ranked = sorted(unique.values(), key=lambda item: _score(item, query), reverse=True)[:limit]
    for item in ranked:
        item["score"] = _score(item, query)
    return {"provider": "bitey-searx-like-core", "results": ranked, "errors": errors, "blocked_providers": list(BLOCKED_TERMS)}
