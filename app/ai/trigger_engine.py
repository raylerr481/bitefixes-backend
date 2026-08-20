"""Dynamic triggers for Bitey's advisory engines.
Triggers request AI/search work; they never execute business actions."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass(frozen=True)
class TriggerPlan:
    names: tuple[str, ...]
    capabilities: tuple[str, ...]
    max_providers: int
    reason: str

def evaluate(*, message: str, intent: Dict[str, Any] | None = None,
             knowledge: Any = None, memory: Dict[str, Any] | None = None,
             language: str | None = None) -> TriggerPlan:
    intent = intent or {}; memory = memory or {}
    text = str(message or '').strip().lower()
    confidence = float(intent.get('confidence', 0) or 0)
    intent_name = intent.get('intent')
    knowledge_gap = bool(intent.get('knowledge_gap')) or knowledge in (None, {}, [], '')
    complex_query = len(text) >= 220 or text.count(' y ') >= 2 or text.count(' and ') >= 2 or text.count(' e ') >= 2
    procedural = any(x in text for x in ('como hago','como hacer','como instalar','como reparar','como configurar','how do i','how to','como faco','como fazer'))
    fresh = any(x in text for x in ('actual','actualmente','hoy','reciente','precio actual','version actual','latest','today','current','agora','atual'))
    followup = bool(intent.get('context_inherited') or memory.get('last_intent'))
    names: List[str] = []; capabilities: List[str] = []; reasons: List[str] = []
    if confidence < 0.70 and not intent_name:
        names.append('LOW_CONFIDENCE'); capabilities.append('semantic_analysis'); reasons.append('low_confidence')
    if knowledge_gap and not fresh:
        names.append('KNOWLEDGE_GAP'); capabilities.append('general_reasoning'); reasons.append('knowledge_gap')
    if fresh:
        names.append('FRESH_INFORMATION'); capabilities.append('web_search'); reasons.append('fresh_information')
    if complex_query:
        names.append('COMPLEX_QUERY'); capabilities.append('general_reasoning'); reasons.append('complex_query')
    if procedural:
        names.append('PROCEDURAL_ADVISORY'); capabilities.append('general_reasoning'); reasons.append('procedural_advisory')
    if followup:
        names.append('CONTEXTUAL_FOLLOWUP'); reasons.append('contextual_followup')
    names = list(dict.fromkeys(names)); capabilities = list(dict.fromkeys(capabilities))
    return TriggerPlan(tuple(names), tuple(capabilities), 2 if (complex_query or len(names) >= 2) else 1, ','.join(reasons) or 'core_sufficient')
