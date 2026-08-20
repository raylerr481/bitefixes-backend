"""Bitey Concept + Learning Engine.

Turns unfamiliar user language into normalized concepts without requiring a
new hard-coded intent rule for every spelling, synonym, or colloquial phrase.
The engine is deliberately conservative: it can propose concepts and store
validated learning events, but it never promotes an unverified external claim
into authoritative knowledge by itself.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List, Optional

from app.database.supabase import database


@dataclass
class ConceptMatch:
    concept: str
    domain: str
    confidence: float
    evidence: List[str]
    variants: List[str]
    diagnostic_signals: List[str]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


CONCEPT_LEXICON: Dict[str, Dict[str, Any]] = {
    "mobile_device": {
        "domain": "mobile",
        "variants": ["celular", "celulares", "movil", "moviles", "telefone", "telefones", "telefono", "telefonos", "phone", "smartphone", "android", "iphone"],
        "signals": ["mobile_repair"],
    },
    "screen_damage": {
        "domain": "mobile",
        "variants": ["pantalla", "tela", "display", "screen", "vidrio", "vidrio roto", "pantalla rota", "tela quebrada", "display quebrado"],
        "signals": ["screen_damage", "mobile_repair"],
    },
    "boot_loop": {
        "domain": "mobile",
        "variants": ["bootloop", "boot loop", "bootloopando", "reinicia sin parar", "reiniciando sin parar", "fica reiniciando", "reiniciando sempre", "loop de inicializacao", "loop de inicialização"],
        "signals": ["boot_failure", "mobile_repair"],
    },
    "computer_device": {
        "domain": "computer",
        "variants": ["computadora", "computadoras", "ordenador", "ordenadores", "pc", "notebook", "laptop", "portatil", "portátil"],
        "signals": ["computer_repair"],
    },
    "networking": {
        "domain": "network",
        "variants": ["wifi", "wi fi", "rede", "red", "roteador", "router", "internet", "lan", "wireless"],
        "signals": ["network_configuration"],
    },
    "cctv": {
        "domain": "security",
        "variants": ["camera", "cameras", "camara", "camaras", "cctv", "monitoramento", "monitorizacion", "camara de seguridad", "camera de seguranca"],
        "signals": ["cctv_installation"],
    },
}


def normalize_text(text: Any) -> str:
    value = str(text or "").lower().strip()
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _token_similarity(token: str, variants: Iterable[str]) -> Optional[str]:
    if len(token) < 4:
        return None
    best = max(((variant, _similar(token, variant)) for variant in variants), key=lambda item: item[1], default=(None, 0.0))
    return best[0] if best[1] >= 0.84 else None


def _lexicon_match(text: str, variants: List[str]) -> List[str]:
    found: List[str] = []
    tokens = text.split()
    for variant in variants:
        if variant in text:
            found.append(variant)
    for token in tokens:
        match = _token_similarity(token, variants)
        if match and match not in found:
            found.append(match)
    return found


def _stored_concepts(text: str, domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """Read validated concepts when the optional learning tables exist."""
    try:
        query = database.table("bitey_concepts").select("*").eq("is_active", True)
        if domain:
            query = query.eq("domain", domain)
        rows = query.execute().data or []
        normalized = normalize_text(text)
        return [row for row in rows if any(normalize_text(v) in normalized for v in (row.get("variants") or []))]
    except Exception:
        return []


def understand(message: str, *, context: Optional[Dict[str, Any]] = None, domain: Optional[str] = None) -> Dict[str, Any]:
    """Infer concepts from known lexicon, learned concepts and fuzzy language."""
    text = normalize_text(message)
    candidates: List[ConceptMatch] = []

    for concept, spec in CONCEPT_LEXICON.items():
        if domain and spec["domain"] != domain:
            continue
        evidence = _lexicon_match(text, spec["variants"])
        if not evidence:
            continue
        exact = sum(1 for item in evidence if item in text)
        confidence = min(0.96, 0.62 + 0.08 * min(len(evidence), 3) + (0.10 if exact else 0.0))
        candidates.append(ConceptMatch(concept, spec["domain"], round(confidence, 4), evidence, spec["variants"], spec["signals"]))

    for row in _stored_concepts(text, domain):
        candidates.append(ConceptMatch(
            concept=str(row.get("concept")),
            domain=str(row.get("domain") or domain or "general"),
            confidence=float(row.get("confidence") or 0.75),
            evidence=list(row.get("matched_variants") or row.get("variants") or []),
            variants=list(row.get("variants") or []),
            diagnostic_signals=list(row.get("diagnostic_signals") or []),
        ))

    # Context lets short follow-ups inherit a previously established domain.
    if not candidates and context:
        previous = context.get("concept") or context.get("last_concept")
        if previous:
            candidates.append(ConceptMatch(str(previous), str(context.get("domain") or "general"), 0.72, ["conversation_context"], [], []))

    candidates.sort(key=lambda item: item.confidence, reverse=True)
    primary = candidates[0].as_dict() if candidates else None
    return {
        "known": bool(primary),
        "concept": primary,
        "candidates": [item.as_dict() for item in candidates[:5]],
        "normalized": text,
        "knowledge_gap": not bool(primary),
    }


def propose_learning(message: str, *, intent: Optional[str], language: str, answer: Optional[str] = None, evidence: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Create a reviewable learning proposal. No automatic authority is granted."""
    understood = understand(message)
    return {
        "status": "known" if understood["known"] else "candidate",
        "message": message,
        "language": language,
        "intent": intent,
        "concept": understood.get("concept"),
        "evidence": evidence or [],
        "answer": answer,
        "validated": False,
        "requires_validation": not understood["known"],
    }


def record_learning(proposal: Dict[str, Any], *, company_id: Optional[int] = None, conversation_id: Optional[str] = None) -> bool:
    """Persist a learning event when the optional table is available.

    Failure is intentionally non-fatal so learning never breaks customer chat.
    """
    try:
        database.table("bitey_learning_events").insert({
            "company_id": company_id,
            "conversation_id": conversation_id,
            "message": proposal.get("message"),
            "language": proposal.get("language"),
            "intent": proposal.get("intent"),
            "concept": proposal.get("concept"),
            "evidence": proposal.get("evidence") or [],
            "validated": bool(proposal.get("validated")),
        }).execute()
        return True
    except Exception as error:
        print("[LEARNING INFO] optional persistence unavailable:", error)
        return False
