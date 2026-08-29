"""Bitey Intelligent Problem Understanding Engine V1.

Evidence-first analysis layer. It separates customer identity from incident
identity, compares the current message with active/historical incidents, and
returns an auditable classification instead of relying on one keyword.
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, Optional

from app.services.problem_identity_service import analyze_problem

STOP = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
    "que", "y", "o", "a", "en", "con", "por", "para", "mi", "mis", "me", "se",
    "es", "esta", "este", "un", "como", "puedo", "quiero", "necesito", "tengo",
    "the", "a", "an", "is", "my", "i", "it", "and", "or", "to", "in", "with",
}

CATEGORY_ALIASES = {
    "malware": {"virus", "malware", "troyano", "trojan", "spyware", "adware", "infectado", "infectada", "anuncios", "publicidad", "popup", "popups"},
    "slow_performance": {"lento", "lenta", "lentitud", "lag", "traba", "trava", "congela", "congelado", "desempeno", "rendimiento"},
    "network": {"wifi", "internet", "red", "conexion", "conexao", "router", "roteador"},
    "power": {"bateria", "carga", "cargar", "enciende", "prende", "apagando"},
    "screen": {"pantalla", "display", "tela", "vidrio", "cristal"},
}


def norm(text: Any) -> str:
    raw = str(text or "").lower()
    raw = "".join(c for c in unicodedata.normalize("NFD", raw) if unicodedata.category(c) != "Mn")
    return " ".join(re.findall(r"[a-z0-9]+", raw))


def tokens(text: Any) -> set[str]:
    return {t for t in norm(text).split() if t not in STOP and len(t) > 1}


def semantic_similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    overlap = len(ta & tb) / max(1, len(ta | tb))
    sequence = SequenceMatcher(None, norm(a), norm(b)).ratio()
    return round(min(1.0, overlap * 0.7 + sequence * 0.3), 4)


def _category_from_text(text: str) -> Optional[str]:
    t = tokens(text)
    scores = {category: len(t & words) for category, words in CATEGORY_ALIASES.items()}
    best = max(scores, key=scores.get) if scores else None
    return best if best and scores[best] else None


def _same_device(current: Dict[str, Any], historical: Dict[str, Any]) -> bool:
    c = norm(current.get("device") or "")
    h = norm(historical.get("device_label") or historical.get("device") or "")
    if c and h:
        return c == h or c in h or h in c
    cp = norm(current.get("platform") or "")
    hp = norm(historical.get("device_platform") or historical.get("platform") or "")
    return bool(cp and hp and cp == hp)


def understand_problem(
    message: str,
    *,
    current_intent: Optional[str] = None,
    active_intent: Optional[str] = None,
    active_problem: Optional[str] = None,
    active_device: Optional[str] = None,
    historical_problems: Optional[Iterable[dict]] = None,
) -> Dict[str, Any]:
    base = analyze_problem(
        message=message,
        current_intent=current_intent,
        active_intent=active_intent,
        active_problem=active_problem,
        active_device=active_device,
    )
    history = list(historical_problems or [])
    current_category = base.get("category") or _category_from_text(message)
    candidates = []

    for item in history:
        similarity = semantic_similarity(message, item.get("problem_summary") or item.get("category") or "")
        same_device = _same_device(base, item)
        same_category = bool(current_category and norm(current_category) == norm(item.get("category") or ""))
        same_intent = bool(base.get("intent") and norm(base.get("intent")) == norm(item.get("intent") or ""))
        score = similarity
        if same_category:
            score += 0.22
        if same_device:
            score += 0.20
        if same_intent:
            score += 0.12
        candidates.append({
            "id": item.get("id"),
            "fingerprint": item.get("fingerprint"),
            "similarity": round(min(1.0, score), 4),
            "same_category": same_category,
            "same_device": same_device,
            "same_intent": same_intent,
            "state": item.get("state"),
        })

    candidates.sort(key=lambda x: x["similarity"], reverse=True)
    best = candidates[0] if candidates else None

    # Evidence hierarchy: explicit device change is strong NEW_PROBLEM evidence;
    # matching device/category/history is strong continuation evidence.
    state = base.get("state", "NEW_PROBLEM")
    if best:
        if best["similarity"] >= 0.78 and best["same_device"] and best["same_category"]:
            state = "REOPENED_PROBLEM" if best.get("state") == "CLOSED" else "CONTINUATION"
        elif best["similarity"] >= 0.62 and (best["same_device"] or best["same_category"]):
            state = "RELATED_PROBLEM"

    # A clearly different device plus a concrete category should not inherit
    # an old incident merely because the customer is the same.
    if active_device and base.get("device") and not _same_device(base, {"device_label": active_device, "platform": base.get("platform")}):
        state = "NEW_PROBLEM"

    confidence = max(float(base.get("confidence", 0) or 0), (best["similarity"] if best else 0.0))
    return {
        **base,
        "state": state,
        "is_new": state == "NEW_PROBLEM",
        "is_continuation": state == "CONTINUATION",
        "is_reopened": state == "REOPENED_PROBLEM",
        "is_related": state == "RELATED_PROBLEM",
        "category": current_category,
        "confidence": round(min(0.99, confidence), 4),
        "historical_match": best,
        "historical_candidates": candidates[:5],
        "analysis_version": "problem-understanding-v1",
        "reasoning": {
            "device_evidence": bool(base.get("device") or base.get("platform")),
            "category_evidence": bool(current_category),
            "history_compared": bool(history),
            "history_candidate_count": len(candidates),
        },
    }
