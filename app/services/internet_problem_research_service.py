"""Bitey Internet Problem Research Engine.

Per-problem comparative research against public web sources. The engine is
provider-light: it uses DuckDuckGo HTML search through httpx and ranks results
locally. It never treats a search result as proof; it returns evidence,
confidence and source metadata for the decision layer.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import quote, urlparse

import httpx


STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "your",
    "you", "are", "how", "what", "why", "can", "que", "para", "con", "una",
    "uno", "los", "las", "del", "por", "como", "tiene", "está", "esta", "sus",
    "una", "un", "de", "en", "es", "me", "mi", "el", "la", "y", "o", "se",
}
TRUSTED_DOMAINS = {
    "support.google.com": 1.35,
    "android.com": 1.30,
    "source.android.com": 1.30,
    "support.microsoft.com": 1.30,
    "learn.microsoft.com": 1.25,
    "support.apple.com": 1.30,
    "cisa.gov": 1.30,
    "nvd.nist.gov": 1.30,
    "owasp.org": 1.30,
    "github.com": 1.05,
}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[\wÀ-ÿ.-]{3,}", (text or "").lower())
    return {w for w in words if w not in STOPWORDS}


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _extract_results(html: str) -> List[Dict[str, str]]:
    # DuckDuckGo HTML result blocks are deliberately parsed conservatively.
    results: List[Dict[str, str]] = []
    blocks = re.findall(r'<div[^>]+class="result[^>]*>(.*?)(?=<div[^>]+class="result|</body>)', html or "", re.S | re.I)
    for block in blocks[:12]:
        href_match = re.search(r'class="result__a"[^>]+href="([^"]+)"', block, re.I)
        title_match = re.search(r'class="result__a"[^>]*>(.*?)</a>', block, re.I | re.S)
        snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>', block, re.I | re.S)
        if not href_match or not title_match:
            continue
        clean = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()
        results.append({
            "title": clean(title_match.group(1)),
            "url": href_match.group(1),
            "snippet": clean(snippet_match.group(1) if snippet_match else ""),
        })
    return results


def _build_query(message: str, problem: Dict[str, Any], language: str) -> str:
    parts = [
        str(problem.get("category") or ""),
        str(problem.get("intent") or ""),
        str(problem.get("device") or ""),
        str(problem.get("platform") or ""),
        " ".join(problem.get("symptoms") or []),
        message,
    ]
    query = " ".join(p for p in parts if p).strip()
    if language == "pt-BR":
        query += " solução diagnóstico"
    elif language == "es":
        query += " diagnóstico solución"
    else:
        query += " diagnosis solution"
    return query[:500]


def research_problem(message: str, problem: Dict[str, Any], language: str = "es", max_results: int = 6) -> Dict[str, Any]:
    """Search, compare and rank public solutions for one concrete problem."""
    query = _build_query(message, problem, language)
    if not query or problem.get("state") == "NEEDS_CLARIFICATION":
        return {"searched": False, "query": query, "matches": [], "best": None, "confidence": 0.0}

    try:
        url = "https://html.duckduckgo.com/html/?q=" + quote(query)
        headers = {"User-Agent": "Bitey/1.0 (+https://bitefixes.com)"}
        with httpx.Client(timeout=8.0, follow_redirects=True, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
        raw = _extract_results(response.text)
    except Exception as exc:
        return {"searched": False, "query": query, "matches": [], "best": None, "confidence": 0.0, "error": type(exc).__name__}

    target = _tokens(" ".join([
        message,
        str(problem.get("category") or ""),
        str(problem.get("intent") or ""),
        str(problem.get("device") or ""),
        str(problem.get("platform") or ""),
        " ".join(problem.get("symptoms") or []),
    ]))
    ranked = []
    for item in raw:
        evidence = _tokens(item["title"] + " " + item["snippet"])
        overlap = len(target & evidence) / max(1, len(target))
        domain = _domain(item["url"])
        trust = TRUSTED_DOMAINS.get(domain, 0.90)
        score = round(min(1.0, overlap * 0.75 + min(trust / 1.35, 1.0) * 0.25), 4)
        ranked.append({**item, "domain": domain, "match_score": score, "evidence_overlap": round(overlap, 4), "trust_score": trust})

    ranked.sort(key=lambda x: (x["match_score"], x["trust_score"]), reverse=True)
    ranked = ranked[:max_results]
    best = ranked[0] if ranked else None
    return {
        "searched": True,
        "query": query,
        "matches": ranked,
        "best": best,
        "confidence": float(best["match_score"] if best else 0.0),
        "method": "internet_comparative_match_v1",
    }
