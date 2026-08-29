"""Bitey Problem Identity Engine V6.

Maintains a general, evolving problem state. The active problem is a semantic
object rather than a keyword label: each turn may add entities, observations,
hypotheses, goals or evidence, continue the same problem, or create another one.
The language model is consulted when available; deterministic signals remain a
safe fallback and are never allowed to erase a stronger active problem.
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
    if tokens & MOBILE_WORDS: return "mobile"
    if tokens & COMPUTER_WORDS: return "computer"
    return None


def _looks_like_device_only(text: str, device: Dict[str, Optional[str]]) -> bool:
    if not device.get("label"): return False
    problem_tokens = set().union(*(_tokens(p) for values in PROBLEM_PATTERNS.values() for p in values))
    return not bool(_tokens(text) & problem_tokens) and len(_tokens(text)) <= 8


def _semantic_understanding(message: str, active_problem: Optional[str], active_intent: Optional[str], active_device: Optional[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not llm_understand: return {}
    try:
        result = llm_understand(message=message, language=(context or {}).get("language", "es"), context={
            **(context or {}), "last_problem": active_problem, "active_problem": active_problem,
            "last_intent": active_intent, "active_device": active_device,
        }) or {}
        return result if isinstance(result, dict) else {}
    except Exception as error:
        print("[SEMANTIC UNDERSTANDING WARNING]", error)
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
    lexical_category = max(category_scores, key=category_scores.get) if category_scores else None

    semantic = _semantic_understanding(message, active_problem, active_intent, active_device, context)
    coherence = semantic.get("coherence") if isinstance(semantic.get("coherence"), dict) else {}
    relation = str(coherence.get("relation") or "").upper()
    semantic_confidence = float(coherence.get("confidence", semantic.get("confidence", 0)) or 0)
    preserve_active = bool(coherence.get("preserve_active_problem"))
    updated_entities = coherence.get("updated_entities") if isinstance(coherence.get("updated_entities"), dict) else {}
    semantic_category = semantic.get("problem_category") or semantic.get("problem_type")
    semantic_summary = semantic.get("problem_summary")
    hypotheses = semantic.get("hypotheses") if isinstance(semantic.get("hypotheses"), list) else []
    semantic_symptoms = semantic.get("symptoms") if isinstance(semantic.get("symptoms"), list) else []
    semantic_entities = semantic.get("entities") if isinstance(semantic.get("entities"), dict) else {}

    device_only = _looks_like_device_only(text, device)
    # The semantic result can classify a standalone message. This is the key
    # generalization: device type and problem type are separate dimensions.
    category = str(semantic_category or lexical_category or "").strip() or None
    intent = str(semantic.get("intent") or current_intent or active_intent or "").strip() or None

    if active_problem and (device_only or preserve_active or relation in {"CONTINUATION", "ENTITY_UPDATE", "ANSWER_TO_QUESTION"}):
        if active_intent: intent = active_intent
        if not category: category = active_problem

    effective_device = device["label"] or semantic_entities.get("device") or updated_entities.get("device") or active_device
    effective_platform = device["platform"] or semantic_entities.get("platform") or updated_entities.get("platform")
    if not effective_platform and active_device and "android" in _norm(active_device): effective_platform = "android"
    effective_kind = current_kind or active_kind

    active_tokens = _tokens(active_problem)
    overlap = len(tokens & active_tokens) if active_tokens else 0
    same_device = bool(active_device and effective_device and _norm(active_device) == _norm(effective_device))
    device_changed = bool(active_device and device["label"] and not same_device)
    explicit_reopen = any(marker in text for marker in REOPEN_MARKERS)
    explicit_continuation = any(marker in text for marker in CONTINUATION_MARKERS)
    same_problem_domain = bool(category and active_problem and category in active_tokens)

    if relation in {"CONTINUATION", "ENTITY_UPDATE", "ANSWER_TO_QUESTION"} and semantic_confidence >= 0.60 and active_problem:
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

    # If a semantic model says this is a continuation, never downgrade it to a
    # generic device service. Business service resolution remains a later step.
    fingerprint_parts = [category or active_problem or "unknown", _norm(effective_device or effective_platform or "unknown"), _norm(intent or "unknown")]
    fingerprint = sha256("|".join(fingerprint_parts).encode("utf-8")).hexdigest()[:32]

    confidence = max(0.35, min(0.95, 0.35 + (0.25 if category else 0) + (0.15 if effective_device else 0) + (0.10 if intent else 0) + (0.15 if semantic_confidence >= 0.60 else 0)))
    if semantic_confidence > 0: confidence = max(confidence, min(0.99, semantic_confidence))

    return {
        "state": state, "is_new": state == "NEW_PROBLEM", "is_continuation": state == "CONTINUATION",
        "is_reopened": state == "REOPENED_PROBLEM", "is_related": state == "RELATED_PROBLEM",
        "confidence": round(confidence, 3), "category": category, "intent": intent,
        "problem_summary": semantic_summary or category, "hypotheses": hypotheses,
        "symptoms": list(dict.fromkeys(matched + [str(x) for x in semantic_symptoms]))[:30],
        "entities": {**semantic_entities, **updated_entities, "device": effective_device, "platform": effective_platform},
        "device": effective_device, "device_kind": effective_kind, "platform": effective_platform,
        "matched_signals": sorted(set(matched)), "overlap_tokens": overlap, "fingerprint": fingerprint,
        "coherence": {
            "device_only": device_only, "active_problem_preserved": bool((device_only or preserve_active) and active_problem),
            "semantic_relation": relation or None, "semantic_confidence": semantic_confidence,
            "updated_entities": updated_entities,
        },
        "analysis_version": "problem-identity-v6-general-semantic-state",
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
        "problem_summary": (analysis.get("problem_summary") or summary)[:1000],
        "symptoms": analysis.get("symptoms") or analysis.get("matched_signals", []),
        "evidence": {"confidence": analysis.get("confidence"), "overlap_tokens": analysis.get("overlap_tokens", 0), "coherence": analysis.get("coherence", {}), "hypotheses": analysis.get("hypotheses", []), "entities": analysis.get("entities", {}), "analysis_version": analysis.get("analysis_version")},
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
