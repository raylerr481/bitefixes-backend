"""Web/YouTube research for user-requested DIY repair tutorials.

The service is deliberately generic: it derives the search query from the
active problem/entity instead of maintaining device-specific rules.
"""
from __future__ import annotations

import html
import re
from urllib.parse import quote_plus, urlparse

import requests


_TUTORIAL_TERMS = (
    "video", "youtube", "tutorial", "guia", "guía", "como hacer", "cómo hacer",
    "paso a paso", "reparar yo mismo", "hacerlo yo", "repararlo yo", "diy",
)


def tutorial_requested(message: str) -> bool:
    text = str(message or "").strip().lower()
    return any(term in text for term in _TUTORIAL_TERMS)


def _youtube_search_url(query: str) -> str:
    return f"https://www.youtube.com/results?search_query={quote_plus(query)}"


def _web_search(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Best-effort DuckDuckGo HTML search without an API key."""
    try:
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "BiteFixes-Bitey/1.0"},
            timeout=8,
        )
        response.raise_for_status()
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            re.I | re.S,
        )
        results: list[dict[str, str]] = []
        for href, title in pattern.findall(response.text):
            clean_title = re.sub(r"<[^>]+>", "", html.unescape(title)).strip()
            if not clean_title:
                continue
            parsed = urlparse(href)
            if parsed.scheme not in {"http", "https"}:
                continue
            results.append({"title": clean_title, "url": href})
            if len(results) >= limit:
                break
        return results
    except requests.RequestException:
        return []


def build_repair_research(
    *,
    message: str,
    active_problem: str | None = None,
    active_category: str | None = None,
    active_object: str | None = None,
    active_model: str | None = None,
    language: str = "es",
) -> dict:
    """Return web and YouTube tutorial resources for the active repair context."""
    parts = [x for x in (active_object, active_model, active_category, active_problem) if x]
    context = " ".join(parts).strip() or str(message or "").strip()
    suffix = "tutorial reparación paso a paso"
    query = f"{context} {suffix}".strip()
    youtube_query = f"{context} screen repair tutorial" if active_model else query

    return {
        "requested": True,
        "query": query,
        "language": language,
        "youtube": {
            "search_url": _youtube_search_url(youtube_query),
            "results": _web_search(f"site:youtube.com/watch {youtube_query}", limit=5),
        },
        "web": _web_search(query, limit=5),
        "safety": [
            "Confirma el modelo exacto y el tipo de pieza antes de desmontar.",
            "Apaga y desconecta el equipo antes de abrirlo cuando corresponda.",
            "Si hay batería hinchada, calor anormal, humo o daño de red eléctrica, detén el procedimiento y usa un técnico.",
            "Un tutorial es una referencia; no sustituye el manual de servicio ni garantiza que el procedimiento sea seguro para todas las variantes.",
        ],
    }
