"""Unified cognitive state for Bitey conversations.

The state is an orchestration artifact, not a replacement for Supabase.
It gives every cognitive component the same representation of what is known,
what is being solved, what is missing, and what should happen next.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CognitiveState:
    customer_id: Optional[int] = None
    company_id: Optional[int] = None
    conversation_id: Optional[str] = None
    language: str = "pt-BR"
    goal: Optional[str] = None
    active_problem: Optional[str] = None
    problem_state: str = "unknown"
    intent: Optional[str] = None
    service_id: Optional[int] = None
    entity: Dict[str, Any] = field(default_factory=dict)
    known: Dict[str, Any] = field(default_factory=dict)
    missing: List[str] = field(default_factory=list)
    asked: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    next_action: str = "understand"
    confidence: float = 0.0
    source: str = "runtime"

    def merge(self, updates: Dict[str, Any]) -> "CognitiveState":
        """Merge only supplied values; never erase established context by omission."""
        for key, value in updates.items():
            if value is None or key not in self.__dataclass_fields__:
                continue
            if key in {"known", "entity"} and isinstance(value, dict):
                getattr(self, key).update(value)
            elif key in {"missing", "asked", "evidence", "hypotheses", "contradictions", "actions"} and isinstance(value, list):
                setattr(self, key, value)
            else:
                setattr(self, key, value)
        return self

    def record_action(self, action: str, **metadata: Any) -> None:
        self.actions.append({"action": action, **metadata})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_context(cls, context: Dict[str, Any]) -> "CognitiveState":
        state = cls()
        state.merge({k: v for k, v in context.items() if k in cls.__dataclass_fields__})
        return state
