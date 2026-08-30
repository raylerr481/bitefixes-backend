"""Portable, tenant-scoped cognitive state contract for Bitey."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CognitiveState:
    company_id: int
    channel: str
    conversation_id: str
    user_id: Optional[str] = None
    active_problem: Optional[str] = None
    active_goal: Optional[str] = None
    active_service: Optional[str] = None
    known_facts: Dict[str, Any] = field(default_factory=dict)
    new_facts: Dict[str, Any] = field(default_factory=dict)
    missing_facts: List[str] = field(default_factory=list)
    questions_asked: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    next_best_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
