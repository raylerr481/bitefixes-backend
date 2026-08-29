"""Bitey Problem Identity Engine.

Separates customer identity from problem identity and keeps multiple incidents
for the same customer independent. Deterministic first; persistence second.
"""
from __future__ import annotations

from hashlib import sha256
import re
import unicodedata
from typing import Any, Dict, Optional

from app.database.supabase import database

STATES = {"NEW_PROBLEM", "CONTINUATION", "REOPENED_PROBLEM", "RELATED_PROBLEM", "NEEDS_CLARIFICATION"}

PLATFORM_WORDS = {
    "android": "android", "ios": "ios", "iphone": "ios", "windows": "windows",
    "macos": "macos", "linux": "linux", "ipad": "ios",
}

DEVICE_PATTERNS = [
    (r"\b(redmi\s+note\s+[0-9]+[a-z0-9-]*)\b", "mobile"),
    (r"\b(redmi\s+[a-z0-9-]+)\b", "mobile"),
    (r"\b(iphone\s*[0-9]+(?:\s*(?:pro|max|plus|mini))?)\b", "mobile"),
    (r"\b(galaxy\s+[a-z0-9][a-z0-9 -]*)\b", "mobile"),
    (r"\b(pixel\s+[0-9]+(?:\s*(?:pro|xl))?)\b", "mobile"),
    (r"\b(laptop|notebook|computador|computadora|pc|ordenador)\b", "computer"),
    (r"\b(celular|telefono|telefone|movil|móvil|smartphone|phone|mobile|tablet|tableta)\b", "mobile"),
]

PROBLEM_PATTERNS = {
    "malware": ["virus", "malware", "troyano", "trojan", "spyware", "adware", "infectado", "infectada", "infectado", "anuncios", "publicidad", "popup", "popups", "aplicaciones desconocidas"],
    "slow_performance": ["lento", "lenta", "lentitud", "slow", "se traba", "trava", "lag", "muy lento"],
    "screen": ["pantalla", "display", "tela", "vidrio", "cristal"],
    "network": ["wifi", "internet", "red", "router", "roteador", "conexion", "conexión"],
    "power": ["bateria", "batería", "no carga", "carga", "apagando", "no enciende", "no prende"],
    "software": ["aplicacion", "aplicación", "app", "error", "actualizacion", "actualización", "sistema"],
}

REOPEN_MARKERS = ("volvio", "volvió", "regreso", "regresó", "reaparecio", "reapareció", "otra vez", "again", "de novo", "novamente", "otra vez")
CONTINUATION_MARKERS = ("sigue", "continua", "continúa", "todavia", "todavía", "aun", "aún", "igual", "mismo", "eso", "este problema", "el problema")


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return " ".join(re.findall(r"[a-z0-9]+", text))


def _tokens(value: Any) -> set[str]:
    return set(_norm(value).split())


def extract_device(message: str) -> Dict[str, Optional[str]]:
    text = _norm(message)
    for pattern, kind in DEVICE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            label = re.sub(r"\s+", " ", match.group(1)).strip()
            platform = next((p for p, canonical in PLATFORM_WORDS.items() if re.search(rf"\b{re.escape(p)}\b", text)), None)
            return {"label": label, "kind": kind, "platform": platform}
    platform = next((canonical for word, canonical in PLATFORM_WORDS.items() if re.search(rf"\b{re.escape(word)}\b", text)), None)
    return {"label": None, "kind": "mobile" if platform == "android" else None, "platform": platform}


def analyze_problem(message: str, current_intent: Optional[str] = None, active_intent: Optional[str] = None, active_problem: Optional[str] = None, active_device: Optional[str] = None) -> Dict[str, Any]:
    """Return structured evidence, entities, fingerprint inputs and confidence."""
    text = _norm(message)
    tokens = _tokens(message)
    device = extract_device(message)

    category_scores: Dict[str, int] = {}
    matched: list[str] = []
    for category, patterns in PROBLEM_PATTERNS.items():
        for phrase in patterns:
            if _norm(phrase) in text:
                category_scores[category] = category_scores.get(category, 0) + (3 if len(phrase.split()) > 1 else 2)
                matched.append(phrase)

    category = max(category_scores, key=category_scores.get) if category_scores else None
    intent = current_intent or active_intent
    if category == "malware" and device["kind"] == "mobile":
        intent = "mobile_repair"
    elif category == "malware" and device["kind"] == "computer":
        intent = "computer_repair"

    active_tokens = _tokens(active_problem)
    overlap = len(tokens & active_tokens) if active_tokens else 0
    same_device = bool(active_device and device["label"] and _norm(active_device) == _norm(device["label"]))
    device_changed = bool(active_device and device["label"] and not same_device)
    explicit_reopen = any(marker in text for marker in REOPEN_MARKERS)
    explicit_continuation = any(marker in text for marker in CONTINUATION_MARKERS)

    fingerprint_parts = [category or "unknown", intent or "unknown", _norm(device["label"] or active_device or device["platform"] or "unknown")]
    # Malware on Android and malware on a laptop are deliberately different incidents.
    fingerprint = sha256("|".join(fingerprint_parts).encode("utf-8")).hexdigest()[:32]

    confidence = 0.35
    if category:
        confidence += 0.25
    if device["platform"] or device["label"]:
        confidence += 0.20
    if intent:
        confidence += 0.15
    confidence = min(0.99, confidence)

    if active_intent and intent and intent != active_intent:
        state = "NEW_PROBLEM"
    elif device_changed:
        state = "NEW_PROBLEM"
    elif explicit_reopen and (same_device or not active_device):
        state = "REOPENED_PROBLEM"
    elif active_problem and (same_device or not active_device) and (overlap >= 1 or explicit_continuation or category == _norm(active_problem)):
        state = "CONTINUATION"
    elif active_problem and category and overlap >= 1:
        state = "RELATED_PROBLEM"
    elif active_problem and not category and not device["label"]:
        state = "NEEDS_CLARIFICATION"
    else:
        state = "NEW_PROBLEM"

    return {
        "state": state,
        "is_new": state == "NEW_PROBLEM",
        "is_continuation": state == "CONTINUATION",
        "is_reopened": state == "REOPENED_PROBLEM",
        "is_related": state == "RELATED_PROBLEM",
        "confidence": round(confidence, 3),
        "category": category,
        "intent": intent,
        "device": device["label"],
        "device_kind": device["kind"],
        "platform": device["platform"],
        "matched_signals": sorted(set(matched)),
        "overlap_tokens": overlap,
        "fingerprint": fingerprint,
        "analysis_version": "problem-identity-v2",
    }


def classify_problem(message: str, current_intent: Optional[str] = None, active_intent: Optional[str] = None, active_problem: Optional[str] = None, active_device: Optional[str] = None) -> Dict[str, Any]:
    return analyze_problem(message, current_intent, active_intent, active_problem, active_device)


def find_customer_problems(customer_id: int, company_id: Optional[int] = None, limit: int = 20) -> list[dict]:
    try:
        query = database.table("bitey_problems").select("*").eq("customer_id", customer_id).order("last_seen_at", desc=True).limit(limit)
        if company_id is not None:
            query = query.eq("company_id", company_id)
        result = query.execute()
        return result.data or []
    except Exception as error:
        print("[PROBLEM HISTORY WARNING]", error)
        return []


def persist_problem(*, company_id: int, customer_id: int, conversation_id: Optional[int], ticket_id: Optional[int], analysis: Dict[str, Any], summary: str) -> Optional[dict]:
    """Upsert the problem identity. Never creates a second row for the same fingerprint."""
    fingerprint = analysis.get("fingerprint")
    if not fingerprint:
        return None
    payload = {
        "company_id": company_id,
        "customer_id": customer_id,
        "conversation_id": conversation_id,
        "ticket_id": ticket_id,
        "fingerprint": fingerprint,
        "state": analysis.get("state", "NEW_PROBLEM"),
        "category": analysis.get("category"),
        "intent": analysis.get("intent"),
        "device_label": analysis.get("device"),
        "device_platform": analysis.get("platform"),
        "problem_summary": summary[:1000],
        "symptoms": analysis.get("matched_signals", []),
        "evidence": {"confidence": analysis.get("confidence"), "overlap_tokens": analysis.get("overlap_tokens", 0), "analysis_version": analysis.get("analysis_version")},
        "confidence": analysis.get("confidence", 0),
        "last_seen_at": "now()",
        "updated_at": "now()",
    }
    try:
        existing = database.table("bitey_problems").select("*").eq("customer_id", customer_id).eq("fingerprint", fingerprint).limit(1).execute()
        if existing.data:
            row_id = existing.data[0]["id"]
            payload.pop("company_id", None)
            payload.pop("customer_id", None)
            payload.pop("fingerprint", None)
            # PostgREST does not evaluate SQL strings such as now() in JSON payloads; timestamps are omitted here.
            payload.pop("last_seen_at", None)
            payload.pop("updated_at", None)
            updated = database.table("bitey_problems").update(payload).eq("id", row_id).execute()
            return updated.data[0] if updated.data else existing.data[0]
        payload.pop("last_seen_at", None)
        payload.pop("updated_at", None)
        created = database.table("bitey_problems").insert(payload).execute()
        return created.data[0] if created.data else None
    except Exception as error:
        print("[PROBLEM PERSISTENCE WARNING]", error)
        return None
