"""Context-first evidence resolution primitives used by Bitey's cognitive layer.

The resolver deliberately does not know device brands/models. It resolves short
answers from the pending question before interpreting them as new symptoms.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

EvidenceType = Literal["model", "os_version", "symptom", "object", "request", "unknown"]

# Terms are matched as complete words/phrases. In particular, `red` must not
# match the beginning of `redmi`.
_SIGNAL_GROUPS: dict[str, tuple[str, ...]] = {
    "connectivity": ("wifi", "wi-fi", "internet", "red", "conexion", "conexión", "sin señal", "bluetooth", "ethernet"),
    "performance": ("lento", "lenta", "lentitud", "se congela", "congelado", "rendimiento", "slow", "freezes", "lag"),
    "power": ("bateria", "batería", "no carga", "carga lento", "se apaga", "se descarga", "calienta", "sobrecalienta"),
    "display": ("pantalla", "display", "lcd", "touch", "táctil", "tactil", "brillo", "no muestra", "quebrada", "quebrado"),
    "startup": ("no enciende", "no inicia", "no arranca", "no prende", "pantalla negra", "boot", "arranque"),
}

_FIELD_RE = {
    "model": re.compile(r"\b(?:modelo|model)\b", re.I),
    "os_version": re.compile(r"\b(?:versi[oó]n|version)\b", re.I),
    "symptom": re.compile(r"\b(?:qu[eé]|qué)\b.*\b(?:ocurre|pasa|problema|s[ií]ntoma)\b", re.I),
}


def _phrase_present(text: str, phrase: str) -> bool:
    """Match a phrase without substring false positives."""
    pattern = r"(?<![\wÀ-ÿ])" + re.escape(phrase) + r"(?![\wÀ-ÿ])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def classify_signals(text: str) -> list[str]:
    """Return signal groups using word-boundary semantics."""
    return [
        group for group, terms in _SIGNAL_GROUPS.items()
        if any(_phrase_present(text, term) for term in terms)
    ]


def infer_pending_field(question: str) -> str | None:
    for field, pattern in _FIELD_RE.items():
        if pattern.search(question):
            return field
    return None


def looks_like_short_answer(text: str) -> bool:
    words = re.findall(r"[\wÀ-ÿ]+", text.strip())
    return 0 < len(words) <= 8


@dataclass(frozen=True)
class EvidenceDecision:
    evidence_type: EvidenceType
    field: str | None
    value: str | None
    relation: Literal["ANSWER_TO_PENDING", "NEW_EVIDENCE", "AMBIGUOUS"]


def resolve_evidence(current_message: str, pending_question: str | None = None) -> EvidenceDecision:
    """Resolve current evidence using the pending question first.

    This function intentionally has no device/model dictionary. If the agent
    just asked for a model, a short answer is treated as model evidence unless
    it contains an explicit symptom that contradicts that interpretation.
    """
    text = current_message.strip()
    signals = classify_signals(text)
    pending_field = infer_pending_field(pending_question) if pending_question else None

    if pending_field and looks_like_short_answer(text) and not signals:
        return EvidenceDecision("model" if pending_field == "model" else "unknown", pending_field, text, "ANSWER_TO_PENDING")

    if signals:
        return EvidenceDecision("symptom", None, max(signals, key=lambda x: len(x)), "NEW_EVIDENCE")

    return EvidenceDecision("unknown", None, text or None, "AMBIGUOUS")
