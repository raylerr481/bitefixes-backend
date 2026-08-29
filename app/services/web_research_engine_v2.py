"""Bitey Web Research Engine V2.

Free, provider-light comparative research layer. It generates several
problem-specific queries, searches public web results, ranks evidence by
relevance/source quality/diversity, and detects conflicting recommendations.
Search results are evidence only; they never become a diagnosis by themselves.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import quote, urlparse

import httpx

STOPWORDS = {
    "the","and","for","with","that","this","from","into","your","you","are","how","what","why","can",
    "que","para","com","uma","um","dos","das","de","do","da","em","no","na","por","como","tem",
    "tiene","esta","está","sus","una","uno","los","las","del","es","me","mi","el","la","y","o","se",
}

DOMAIN_WEIGHTS = {
    "support.google.com": 1.40, "android.com": 1.35, "source.android.com": 1.35,
    "xiaomi.com": 1.30, "mi.com": 1.30, "support.microsoft.com": 1.30,
    "learn.microsoft.com": 1.28, "support.apple.com": 1.30, "cisa.gov": 1.35,
    "nvd.nist.gov": 1.35, "owasp.org": 1.30, "github.com": 1.05,
}


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[\wÀ-ÿ.-]{3,}", (text or "").lower()) if w not in STOPWORDS}


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def _extract(html: str) -> List[Dict[str, str]]:
    blocks = re.findall(r'<div[^>]+class="result[^>]*>(.*?)(?=<div[^>]+class="result|</body>)', html or "", re.S | re.I)
    out: List[Dict[str, str]] = []
    for block in blocks[:15]:
        href = re.search(r'class="result__a"[^>]+href="([^"]+)"', block, re.I)
        title = re.search(r'class="result__a"[^>]*>(.*?)</a>', block, re.I | re.S)
        snippet = re.search(r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>', block, re.I | re.S)
        if href and title:
            out.append({"title": _clean(title.group(1)), "url": href.group(1), "snippet": _clean(snippet.group(1) if snippet else "")})
    return out


def _queries(message: str, problem: Dict[str, Any], language: str) -> List[str]:
    category = str(problem.get("category") or "")
    device = str(problem.get("device") or "")
    platform = str(problem.get("platform") or "")
    symptoms = " ".join(problem.get("symptoms") or [])
    base = " ".join(x for x in (category, device, platform, symptoms, message) if x).strip()
    suffix = {"pt-BR": "diagnóstico solução segura", "es": "diagnóstico solución segura", "en": "diagnosis safe solution"}.get(language, "diagnosis safe solution")
    variants = [
        f"{base} {suffix}",
        f"{device} {platform} {category} official support",
        f"{category} {symptoms} prevention remediation",
        f"{base} troubleshooting",
    ]
    return list(dict.fromkeys(q[:450] for q in variants if q.strip()))


def _risk(text: str) -> str:
    t = (text or "").lower()
    if any(x in t for x in ("factory reset", "wipe data", "unlock bootloader", "flash rom", "root device", "disable security")):
        return "high"
    if any(x in t for x in ("adb", "developer options", "recovery mode", "permissions")):
        return "medium"
    return "low"


def research_problem_v2(message: str, problem: Dict[str, Any], language: str = "es", max_results: int = 8) -> Dict[str, Any]:
    if not message or problem.get("state") == "NEEDS_CLARIFICATION":
        return {"searched": False, "queries": [], "matches": [], "best": None, "confidence": 0.0, "contradictions": []}
    queries = _queries(message, problem, language)
    target = _tokens(" ".join([message, str(problem.get("category") or ""), str(problem.get("device") or ""), str(problem.get("platform") or ""), " ".join(problem.get("symptoms") or [])]))
    candidates: Dict[str, Dict[str, Any]] = {}
    headers = {"User-Agent": "Bitey/2.0 (+https://bitefixes.com)"}
    errors = []
    try:
        with httpx.Client(timeout=8.0, follow_redirects=True, headers=headers) as client:
            for query in queries:
                try:
                    r = client.get("https://html.duckduckgo.com/html/?q=" + quote(query))
                    r.raise_for_status()
                    for item in _extract(r.text):
                        candidates.setdefault(item["url"], {**item, "query_hits": 0})["query_hits"] += 1
                except Exception as exc:
                    errors.append(type(exc).__name__)
    except Exception as exc:
        errors.append(type(exc).__name__)

    ranked: List[Dict[str, Any]] = []
    for item in candidates.values():
        evidence = _tokens(item["title"] + " " + item["snippet"])
        overlap = len(target & evidence) / max(1, len(target))
        domain = _domain(item["url"])
        trust = DOMAIN_WEIGHTS.get(domain, 0.90)
        repeat = min(item["query_hits"] / max(1, len(queries)), 1.0)
        score = min(1.0, overlap * 0.55 + min(trust / 1.40, 1.0) * 0.25 + repeat * 0.20)
        text = item["title"] + " " + item["snippet"]
        ranked.append({**item, "domain": domain, "match_score": round(score, 4), "trust_score": trust, "query_coverage": round(repeat, 4), "risk": _risk(text)})

    ranked.sort(key=lambda x: (x["match_score"], x["trust_score"], x["query_hits"]), reverse=True)
    selected: List[Dict[str, Any]] = []
    domains: set[str] = set()
    for item in ranked:
        if len(selected) >= max_results:
            break
        if item["domain"] in domains and len(domains) < 4:
            continue
        selected.append(item); domains.add(item["domain"])
    for item in ranked:
        if len(selected) >= max_results:
            break
        if item not in selected:
            selected.append(item)

    low, medium, high = [], [], []
    for item in selected:
        if item["risk"] == "high": high.append(item)
        elif item["risk"] == "medium": medium.append(item)
        else: low.append(item)

    # Detect disagreement signals instead of silently merging contradictory advice.
    contradiction_signals = ("do not", "avoid", "never", "recommended", "recommend", "disable", "enable", "reset", "uninstall")
    contradictions = []
    for i, a in enumerate(selected):
        for b in selected[i + 1:]:
            at = (a["title"] + " " + a["snippet"]).lower()
            bt = (b["title"] + " " + b["snippet"]).lower()
            if any(x in at for x in contradiction_signals) and any(x in bt for x in contradiction_signals):
                if _tokens(at) & _tokens(bt):
                    contradictions.append({"source_a": a["url"], "source_b": b["url"], "reason": "potentially conflicting recommendations; requires validation"})
                    if len(contradictions) >= 5:
                        break
        if len(contradictions) >= 5:
            break

    best = selected[0] if selected else None
    confidence = float(best["match_score"] if best else 0.0)
    if contradictions:
        confidence = round(max(0.0, confidence - min(0.15, 0.03 * len(contradictions))), 4)
    return {
        "searched": bool(selected), "queries": queries, "matches": selected, "best": best,
        "confidence": confidence, "source_domains": sorted(domains),
        "risk_buckets": {"low": len(low), "medium": len(medium), "high": len(high)},
        "contradictions": contradictions, "method": "evidence_ranked_multi_query_v2",
        "errors": errors[:5],
    }
