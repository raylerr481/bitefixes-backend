"""Bitey Problem Identity Engine V5.

Determines whether each turn continues, updates, relates to, or replaces an
active problem. A semantic model is used when available; deterministic signals
remain a safe fallback. The engine never depends on a growing list of special
case phrases.
"""
from __future__ import annotations
from hashlib import sha256
import re
import unicodedata
from typing import Any, Dict, Optional
from app.database.supabase import database

try:
    from app.ai.llm_gateway import understand as llm_understand
except Exception:
    llm_understand = None

STATES = {"NEW_PROBLEM", "CONTINUATION", "REOPENED_PROBLEM", "RELATED_PROBLEM", "NEEDS_CLARIFICATION"}
PLATFORM_WORDS = {"android": "android", "ios": "ios", "iphone": "ios", "windows": "windows", "macos": "macos", "linux": "linux", "ipad": "ios"}
MOBILE_WORDS = {"celular", "telefono", "telefone", "movil", "smartphone", "phone", "mobile", "tablet", "android", "iphone", "redmi", "galaxy", "pixel"}
COMPUTER_WORDS = {"laptop", "notebook", "computador", "computadora", "pc", "ordenador", "windows", "macbook"}
DEVICE_PATTERNS = [
    (r"\b(redmi\s+note\s+[0-9]+[a-z0-9-]*)\b", "mobile"),
    (r"\b(redmi\s+[a-z0-9-]+)\b", "mobile"),
    (r"\b(iphone\s*[0-9]+(?:\s*(?:pro|max|plus|mini))?)\b", "mobile"),
    (r"\b(galaxy\s+[a-z0-9][a-z0-9 -]*)\b", "mobile"),
    (r"\b(pixel\s+[0-9]+(?:\s*(?:pro|xl))?)\b", "mobile"),
    (r"\b(laptop|notebook|computador|computadora|pc|ordenador|macbook)\b", "computer"),
    (r"\b(celular|telefono|telefone|movil|smartphone|phone|mobile|tablet|tableta)\b", "mobile"),
]
PROBLEM_PATTERNS = {
    "malware": ["virus", "malware", "troyano", "trojan", "spyware", "adware", "infectado", "infectada", "anuncios", "publicidad", "popup", "popups", "aplicaciones desconocidas"],
    "slow_performance": ["lento", "lenta", "lentitud", "slow", "se traba", "trava", "lag", "muy lento"],
    "screen": ["pantalla", "display", "tela", "vidrio", "cristal"],
    "network": ["wifi", "internet", "red", "router", "roteador", "conexion", "conexión"],
    "power": ["bateria", "batería", "no carga", "carga", "apagando", "no enciende", "no prende"],
    "software": ["aplicacion", "aplicación", "app", "error", "actualizacion", "actualización", "sistema"],
}
REOPEN_MARKERS = ("volvio", "volvió", "regreso", "regresó", "reaparecio", "reapareció", "otra vez", "again", "de novo", "novamente")
CONTINUATION_MARKERS = ("sigue", "continua", "continúa", "todavia", "todavía", "aun", "aún", "igual", "mismo", "eso", "este problema", "el problema")


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return " ".join(re.findall(r"[a-z0-9]+", text))


def _tokens(value: Any) -> set[str]:
    return set(_norm(value).split())


def extract_device(message: str) -> Dict[str, Optional[str]]:
    raw = str(message or "")
    text = _norm(raw)
    for pattern, kind in DEVICE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            label = re.sub(r"\s+", " ", match.group(1)).strip()
            platform = next((canonical for word, canonical in PLATFORM_WORDS.items() if re.search(rf"\b{re.escape(word)}\b", text)), None)
            return {"label": label, "kind": kind, "platform": platform}
    platform = next((canonical for word, canonical in PLATFORM_WORDS.items() if re.search(rf"\b{re.escape(word)}\b", text)), None)
    if platform == "android":
        return {"label": "android phone", "kind": "mobile", "platform": "android"}
    return {"label": None, "kind": None, "platform": platform}


def _device_kind(value: Any) -> Optional[str]:
    tokens = _tokens(value)
    if tokens & MOBILE_WORDS:
        return "mobile"
    if tokens & COMPUTER_WORDS:
        return "computer"
    return None


def _looks_like_device_only(text: str, device: Dict[str, Optional[str]]) -> bool:
    if not device.get("label"):
        return False
    problem_tokens = set().union(*(_tokens(p) for values in PROBLEM_PATTERNS.values() for p in values))
    tokens = _tokens(text)
    return not bool(tokens & problem_tokens) and len(tokens) <= 8


def _semantic_coherence(message: str, active_problem: Optional[str], active_intent: Optional[str], active_device: Optional[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not llm_understand or not active_problem:
        return {}
    try:
        result = llm_understand(message=message, language=(context or {}).get("language", "es"), context={
            **(context or {}),
            "last_problem": active_problem,
            "active_problem": active_problem,
            "last_intent": active_intent,
            "active_device": active_device,
        }) or {}
        coherence = result.get("coherence") if isinstance(result, dict) else None
        return coherence if isinstance(coherence, dict) else {}
    except Exception as error:
        print("[SEMANTIC COHERENCE WARNING]", error)
        return {}


def analyze_problem(message: str, current_intent: Optional[str] = None, active_intent: Optional[str] = None, active_problem: Optional[str] = None, active_device: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    text = _norm(message)
    tokens = _tokens(message)
    device = extract_device(message)
    active_kind = _device_kind(active_device)
    current_kind = device["kind"] or _device_kind(device["label"])
    category_scores: Dict[str, int] = {}
    matched: list[str] = []
    for category, patterns in PROBLEM_PATTERNS.items():
        for phrase in patterns:
            if _norm(phrase) in text:
                category_scores[category] = category_scores.get(category, 0) + (3 if len(phrase.split()) > 1 else 2)
                matched.append(phrase)
    category = max(category_scores, key=category_scores.get) if category_scores else None

    device_only = _looks_like_device_only(text, device)
    semantic = _semantic_coherence(message, active_problem, active_intent, active_device, context)
    relation = str(semantic.get("relation") or "").upper()
    semantic_confidence = float(semantic.get("confidence", 0) or 0)
    preserve_active = bool(semantic.get("preserve_active_problem"))
    updated_entities = semantic.get("updated_entities") if isinstance(semantic.get("updated_entities"), dict) else {}

    # Semantic model has priority for conversational relationship. Lexical
    # detection is retained only as a deterministic safety fallback.
    if preserve_active and active_problem:
        coherent_active_intent = active_intent
    else:
        coherent_active_intent = active_intent

    intent = current_intent or coherent_active_intent
    if category == "malware" and not active_problem:
        if current_kind == "mobile": intent = "mobile_repair"
        elif current_kind == "computer": intent = "computer_repair"
    elif active_problem and (device_only or preserve_active) and active_intent:
        # Never replace an active specific problem with generic device repair
        # merely because the new turn names a device.
        intent = active_intent

    effective_device = device["label"] or updated_entities.get("device") or active_device
    effective_platform = device["platform"] or updated_entities.get("platform")
    if not effective_platform and active_device and "android" in _norm(active_device):
        effective_platform = "android"
    effective_kind = current_kind or active_kind

    active_tokens = _tokens(active_problem)
    overlap = len(tokens & active_tokens) if active_tokens else 0
    same_device = bool(active_device and effective_device and _norm(active_device) == _norm(effective_device))
    device_changed = bool(active_device and device["label"] and not same_device)
    explicit_reopen = any(marker in text for marker in REOPEN_MARKERS)
    explicit_continuation = any(marker in text for marker in CONTINUATION_MARKERS)
    same_problem_domain = bool(category and active_problem and category in active_tokens)

    if relation in {"CONTINUATION", "ENTITY_UPDATE", "ANSWER_TO_QUESTION"} and semantic_confidence >= 0.65 and active_problem:
        state = "CONTINUATION"
    elif relation == "RELATED_PROBLEM" and semantic_confidence >= 0.70 and active_problem:
        state = "RELATED_PROBLEM"
    elif relation == "NEW_PROBLEM" and semantic_confidence >= 0.70:
        state = "NEW_PROBLEM"
    elif relation == "NEEDS_CLARIFICATION" and semantic_confidence >= 0.70:
        state = "NEEDS_CLARIFICATION"
    elif device_only and active_problem:
        state = "CONTINUATION"
    elif device_changed and not preserve_active:
        state = "NEW_PROBLEM"
    elif explicit_reopen and (same_device or not active_device):
        state = "REOPENED_PROBLEM"
    elif active_problem and (same_device or not active_device) and (overlap >= 1 or explicit_continuation or same_problem_domain):
        state = "CONTINUATION"
    elif active_problem and category and overlap >= 1:
        state = "RELATED_PROBLEM"
    elif active_problem and not category and not device["label"]:
        state = "NEEDS_CLARIFICATION"
    else:
        state = "NEW_PROBLEM"

    fingerprint_parts = [category or active_problem or "unknown", intent or active_intent or "unknown", _norm(effective_device or effective_platform or "unknown")]
    fingerprint = sha256("|".join(fingerprint_parts).encode("utf-8")).hexdigest()[:32]

    confidence = 0.35
    if category or active_problem: confidence += 0.25
    if effective_device or effective_platform: confidence += 0.20
    if intent: confidence += 0.15
    if semantic_confidence >= 0.65: confidence = max(confidence, 0.65 + min(0.34, semantic_confidence * 0.34))
    confidence = min(0.99, confidence)

    return {
        "state": state,
        "is_new": state == "NEW_PROBLEM",
        "is_continuation": state == "CONTINUATION",
        "is_reopened": state == "REOPENED_PROBLEM",
        "is_related": state == "RELATED_PROBLEM",
        "confidence": round(confidence, 3),
        "category": category or (active_problem if (device_only or preserve_active) else None),
        "intent": intent,
        "device": effective_device,
        "device_kind": effective_kind,
        "platform": effective_platform,
        "matched_signals": sorted(set(matched)),
        "overlap_tokens": overlap,
        "fingerprint": fingerprint,
        "coherence": {
            "device_only": device_only,
            "active_problem_preserved": bool((device_only or preserve_active) and active_problem),
            "semantic_relation": relation or None,
            "semantic_confidence": semantic_confidence,
            "updated_entities": updated_entities,
        },
        "analysis_version": "problem-identity-v5-semantic-coherence",
    }


def classify_problem(message: str, current_intent: Optional[str] = None, active_intent: Optional[str] = None, active_problem: Optional[str] = None, active_device: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return analyze_problem(message, current_intent, active_intent, active_problem, active_device, context=context)


def find_customer_problems(customer_id: int, company_id: Optional[int] = None, limit: int = 20) -> list[dict]:
    try:
        query = database.table("bitey_problems").select("*").eq("customer_id", customer_id).order("last_seen_at", desc=True).limit(limit)
        if company_id is not None: query = query.eq("company_id", company_id)
        result = query.execute()
        return result.data or []
    except Exception as error:
        print("[PROBLEM HISTORY WARNING]", error)
        return []


def persist_problem(*, company_id: int, customer_id: int, conversation_id: Optional[int], ticket_id: Optional[int], analysis: Dict[str, Any], summary: str) -> Optional[dict]:
    fingerprint = analysis.get("fingerprint")
    if not fingerprint: return None
    payload = {
        "company_id": company_id, "customer_id": customer_id, "conversation_id": conversation_id, "ticket_id": ticket_id,
        "fingerprint": fingerprint, "state": analysis.get("state", "NEW_PROBLEM"), "category": analysis.get("category"),
        "intent": analysis.get("intent"), "device_label": analysis.get("device"), "device_platform": analysis.get("platform"),
        "problem_summary": summary[:1000], "symptoms": analysis.get("matched_signals", []),
        "evidence": {"confidence": analysis.get("confidence"), "overlap_tokens": analysis.get("overlap_tokens", 0), "coherence": analysis.get("coherence", {}), "analysis_version": analysis.get("analysis_version")},
        "confidence": analysis.get("confidence", 0),
    }
    try:
        existing = database.table("bitey_problems").select("*").eq("customer_id", customer_id).eq("fingerprint", fingerprint).limit(1).execute()
        if existing.data:
            row_id = existing.data[0]["id"]
            updates = {k: v for k, v in payload.items() if k not in {"company_id", "customer_id", "fingerprint"}}
            updated = database.table("bitey_problems").update(updates).eq("id", row_id).execute()
            return updated.data[0] if updated.data else existing.data[0]
        created = database.table("bitey_problems").insert(payload).execute()
        return created.data[0] if created.data else None
    except Exception as error:
        print("[PROBLEM PERSISTENCE WARNING]", error)
        return None
