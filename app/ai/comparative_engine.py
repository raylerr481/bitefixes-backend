"""Governed comparative ranking for Bitey answer candidates."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "you",
    "que", "para", "com", "una", "uno", "los", "las", "del", "por", "como",
    "se", "de", "el", "la", "un", "en", "es", "do", "da", "dos", "das",
    "uma", "um", "e", "em", "no", "na", "ao", "os", "as", "mais", "is",
    "are", "to", "of", "a", "an", "in", "on", "it",
}


def _tokens(text: Any) -> set[str]:
    words = re.findall(r"[\wÀ-ÿ]{3,}", str(text or "").lower())
    return {w for w in words if w not in _STOPWORDS}


def _overlap(a: Iterable[str], b: Iterable[str]) -> float:
    left, right = set(a), set(b)
    if not left or not right:
        return 0.0
    return len(left & right) / max(1, len(left | right))


def _score(candidate: Dict[str, Any], query_tokens: set[str], intent: str | None,
           core_confidence: float) -> Dict[str, Any]:
    answer_tokens = _tokens(candidate.get("answer"))
    relevance = _overlap(query_tokens, answer_tokens)
    intent_match = 1.0 if candidate.get("intent") and candidate.get("intent") == intent else 0.0
    authority = float(candidate.get("authority", 0.0) or 0.0)
    core_bonus = min(max(core_confidence, 0.0), 1.0) if candidate.get("source") == "core" else 0.0
    safety = float(candidate.get("safety", 1.0) or 0.0)
    completeness = min(1.0, len(answer_tokens) / 35.0)
    score = (
        relevance * 0.30 + intent_match * 0.15 + authority * 0.15
        + core_bonus * 0.25 + safety * 0.10 + completeness * 0.05
    )
    candidate["score"] = round(max(0.0, min(1.0, score)), 4)
    candidate["signals"] = {
        "relevance": round(relevance, 4), "intent_match": intent_match,
        "authority": authority, "core_bonus": round(core_bonus, 4),
        "safety": safety, "completeness": round(completeness, 4),
    }
    return candidate


def compare_answers(*, message: str, intent: str | None, core_confidence: float,
                    candidates: List[Dict[str, Any]],
                    min_accept_score: float = 0.30) -> Dict[str, Any]:
    """Rank candidates while preserving Core as authority for business actions.

    External AI can supply the conversational answer when Core is weak and the
    external candidate materially outranks it. This does not grant the external
    provider permission to create tickets, quotes, or integrations.
    """
    query_tokens = _tokens(message)
    ranked = [_score(dict(candidate), query_tokens, intent, core_confidence)
              for candidate in candidates if candidate.get("answer")]
    ranked.sort(key=lambda item: (item.get("score", 0.0), item.get("source") == "core"), reverse=True)
    if not ranked:
        return {"status": "no_candidates", "selected": None, "ranked": [], "confidence": 0.0}

    core = next((c for c in ranked if c.get("source") == "core"), None)
    top = ranked[0]
    selected = core or top
    reason = "core_authoritative"
    if top.get("source") != "core" and top.get("score", 0.0) >= min_accept_score:
        core_score = core.get("score", 0.0) if core else 0.0
        margin = top.get("score", 0.0) - core_score
        if core is None or (core_confidence < 0.70 and margin >= 0.10):
            selected = top
            reason = "external_advisory_wins_materially"
    return {
        "status": "compared", "selected": selected,
        "selected_source": selected.get("source"), "reason": reason,
        "confidence": round(float(selected.get("score", 0.0)), 4),
        "candidate_count": len(ranked), "ranked": ranked,
    }
