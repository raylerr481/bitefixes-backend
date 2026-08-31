"""Broad web research for user-requested tutorials.

Generic Bitey capability: when a user asks for a tutorial/video/guide, Bitey
searches broadly and ranks candidate resources using the active cognitive and
business context. YouTube is one source, never the boundary.
"""
from __future__ import annotations

import html
import re
from urllib.parse import quote_plus, urlparse

import requests

_TUTORIAL_TERMS = ("video", "youtube", "tutorial", "guia", "guía", "como hacer", "cómo hacer", "paso a paso", "reparar yo mismo", "hacerlo yo", "repararlo yo", "diy", "manual", "instrucciones", "how to", "walkthrough", "guide")
_TRUST_HINTS = ("ifixit.com", "support.google.com", "support.microsoft.com", "dell.com", "hp.com", "lenovo.com", "samsung.com", "apple.com", "mi.com", "xiaomi.com", "cisco.com", "learn.microsoft.com", "youtube.com")

def tutorial_requested(message: str) -> bool:
    text = str(message or "").strip().lower()
    return any(term in text for term in _TUTORIAL_TERMS)

def _youtube_search_url(query: str) -> str:
    return f"https://www.youtube.com/results?search_query={quote_plus(query)}"

def _web_search(query: str, limit: int = 8) -> list[dict[str, str]]:
    try:
        response = requests.get("https://html.duckduckgo.com/html/", params={"q": query}, headers={"User-Agent": "Bitey-Research/1.0"}, timeout=8)
        response.raise_for_status()
        pattern = re.compile(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
        results: list[dict[str, str]] = []
        for href, title in pattern.findall(response.text):
            clean_title = re.sub(r"<[^>]+>", "", html.unescape(title)).strip()
            if not clean_title:
                continue
            if urlparse(href).scheme not in {"http", "https"}:
                continue
            results.append({"title": clean_title, "url": href})
            if len(results) >= limit:
                break
        return results
    except requests.RequestException:
        return []

def _score_result(result: dict[str, str], context_terms: list[str], tutorial_terms: list[str]) -> int:
    text = f"{result.get('title', '')} {result.get('url', '')}".lower()
    score = sum(12 for term in context_terms if term and term.lower() in text)
    score += sum(5 for term in tutorial_terms if term in text)
    if any(domain in text for domain in _TRUST_HINTS):
        score += 6
    if "youtube.com" in text:
        score += 4
    return score

def _rank(results: list[dict[str, str]], context_terms: list[str], limit: int = 8) -> list[dict[str, str]]:
    unique: dict[str, dict[str, str]] = {}
    for result in results:
        url = result.get("url", "").strip()
        if not url:
            continue
        item = dict(result)
        item["score"] = str(_score_result(item, context_terms, list(_TUTORIAL_TERMS)))
        unique.setdefault(url, item)
    return sorted(unique.values(), key=lambda item: int(item["score"]), reverse=True)[:limit]

def build_repair_research(*, message: str, active_problem: str | None = None, active_category: str | None = None, active_object: str | None = None, active_model: str | None = None, company_name: str | None = None, industry: str | None = None, language: str = "es") -> dict:
    """Search broadly and rank tutorials using cognitive + tenant context."""
    parts = [str(x).strip() for x in (active_object, active_model, active_category, active_problem, industry) if x and str(x).strip()]
    context = " ".join(parts).strip() or str(message or "").strip()
    context_terms = parts
    query_variants = [f"{context} tutorial paso a paso", f"{context} reparación guía", f"{context} how to repair", f"{context} manual de servicio"]
    youtube_variants = [f"{context} repair tutorial", f"{context} reparación paso a paso", f"{context} teardown repair guide"]
    web_results: list[dict[str, str]] = []
    youtube_results: list[dict[str, str]] = []
    for query in query_variants:
        web_results.extend(_web_search(query, limit=8))
    for query in youtube_variants:
        youtube_results.extend(_web_search(f"site:youtube.com/watch {query}", limit=8))
    return {
        "requested": True, "research_mode": "broad_web_and_youtube", "company_name": company_name, "industry": industry,
        "query": query_variants[0], "query_variants": query_variants, "language": language,
        "selection": {"strategy": "context_match + tutorial_relevance + source_quality_hints", "sources": "open_web + YouTube + specialist/official sources when indexed", "note": "Rankings are recommendations, not guarantees. Verify exact model/variant before following instructions."},
        "youtube": {"search_url": _youtube_search_url(youtube_variants[0]), "results": _rank(youtube_results, context_terms, limit=10)},
        "web": _rank(web_results, context_terms, limit=10),
        "safety": ["Confirma el modelo exacto, la variante y la pieza antes de desmontar.", "Apaga y desconecta el equipo antes de abrirlo cuando corresponda.", "Si hay batería hinchada, calor anormal, humo o riesgo eléctrico, detén el procedimiento y usa un técnico.", "Compara más de una fuente cuando el procedimiento sea crítico o irreversible.", "Un tutorial es una referencia y no sustituye el manual de servicio ni garantiza que el procedimiento sea seguro para todas las variantes."],
    }
