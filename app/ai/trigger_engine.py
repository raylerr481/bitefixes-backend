"""Dynamic Bitey trigger engine.

Triggers wake advisory capabilities; they never execute business actions.
External AIs remain the reasoning authorities. Search is requested only when
an explicit external-information need is detected.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List
import re

CAPABILITIES = {
    "LOW_CONFIDENCE": ("semantic_analysis", "general_reasoning"),
    "KNOWLEDGE_GAP": ("rag", "semantic_analysis"),
    "FRESH_INFORMATION": ("web_search", "general_reasoning"),
    "SEARCH_REQUEST": ("web_search", "general_reasoning"),
    "COMPLEX_QUERY": ("general_reasoning", "semantic_analysis"),
    "PROCEDURAL_ADVISORY": ("general_reasoning",),
    "CONFLICT_DETECTED": ("general_reasoning", "web_search"),
    "CONTEXTUAL_FOLLOWUP": ("memory", "semantic_analysis"),
}

@dataclass(frozen=True)
class TriggerPlan:
    names: tuple[str, ...]
    capabilities: tuple[str, ...]
    max_providers: int
    reason: str
    priority: int = 0


def _add(names: List[str], capabilities: List[str], name: str):
    if name not in names:
        names.append(name)
    for capability in CAPABILITIES.get(name, ()):
        if capability not in capabilities:
            capabilities.append(capability)


def _search_requested(text: str) -> bool:
    explicit = (
        "busca en la web", "buscar en la web", "busque en la web", "busca en internet",
        "buscar en internet", "busque en internet", "search the web", "search online",
        "look it up", "look this up", "pesquise na web", "pesquisar na internet"
    )
    if any(term in text for term in explicit):
        return True
    # Postal-code / location lookups are external facts when no matching
    # verified business fact exists. Do not search arbitrary numbers.
    if re.search(r"\b\d{5}-?\d{3}\b", text) and any(
        term in text for term in ("cep", "código postal", "codigo postal", "postal code", "zip")
    ):
        return True
    return False


def evaluate(*, message: str, intent: Dict[str, Any] | None = None,
             knowledge: Any = None, memory: Dict[str, Any] | None = None,
             language: str | None = None, novelty: float = 0.0,
             complexity: float | None = None, conflict: bool = False,
             business_impact: float = 0.0) -> TriggerPlan:
    intent = intent or {}; memory = memory or {}
    text = str(message or '').strip().lower()
    try:
        confidence = max(0.0, min(1.0, float(intent.get('confidence', 0) or 0)))
    except (TypeError, ValueError):
        confidence = 0.0
    intent_name = intent.get('intent')
    knowledge_gap = bool(intent.get('knowledge_gap')) or knowledge in (None, {}, [], '')
    if complexity is None:
        complexity = min(1.0, max(0.0, len(text) / 300 + text.count(' y ') * .12 + text.count(' and ') * .12 + text.count(' e ') * .12))
    fresh = bool(novelty >= .75) or any(x in text for x in (
        'actual','actualmente','hoy','reciente','precio actual','version actual','latest','today','current','agora','atual'
    ))
    search_requested = _search_requested(text)
    procedural = any(x in text for x in (
        'como hago','como hacer','como instalar','como reparar','como configurar','how do i','how to','como faco','como fazer'
    ))
    followup = bool(intent.get('context_inherited') or memory.get('last_intent') or memory.get('active_ticket'))
    names: List[str] = []; capabilities: List[str] = []; reasons: List[str] = []
    if confidence < .70 and not intent_name:
        _add(names, capabilities, 'LOW_CONFIDENCE'); reasons.append('low_confidence')
    if knowledge_gap and not fresh and not search_requested:
        _add(names, capabilities, 'KNOWLEDGE_GAP'); reasons.append('knowledge_gap')
    if fresh:
        _add(names, capabilities, 'FRESH_INFORMATION'); reasons.append('fresh_information')
    if search_requested:
        _add(names, capabilities, 'SEARCH_REQUEST'); reasons.append('explicit_or_structured_search_need')
    if complexity >= .70:
        _add(names, capabilities, 'COMPLEX_QUERY'); reasons.append('complex_query')
    if procedural:
        _add(names, capabilities, 'PROCEDURAL_ADVISORY'); reasons.append('procedural_advisory')
    if conflict:
        _add(names, capabilities, 'CONFLICT_DETECTED'); reasons.append('conflict_detected')
    if followup:
        _add(names, capabilities, 'CONTEXTUAL_FOLLOWUP'); reasons.append('contextual_followup')
    max_providers = 2 if ('COMPLEX_QUERY' in names or 'CONFLICT_DETECTED' in names or len(names) >= 2) else 1
    priority = 120 if 'SEARCH_REQUEST' in names else (110 if 'CONFLICT_DETECTED' in names else (100 if names else 0))
    return TriggerPlan(tuple(names), tuple(capabilities), max_providers, ','.join(reasons) or 'core_sufficient', priority)
