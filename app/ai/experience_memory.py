"""Experience memory for Bitey's case-based learning.

Experiences are evidence about what happened in a real case. They are not
truth by themselves and are never promoted directly to trusted knowledge.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Experience:
    case_id: str
    problem: str
    symptoms: List[str] = field(default_factory=list)
    facts: Dict[str, Any] = field(default_factory=dict)
    action: str | None = None
    outcome: str | None = None
    success: bool | None = None
    source: str = "case"
    confidence: float = 0.0


class ExperienceMemory:
    def __init__(self) -> None:
        self._cases: Dict[str, Experience] = {}

    def record(self, experience: Experience) -> Experience:
        self._cases[experience.case_id] = experience
        return experience

    def similar(self, problem: str, symptoms: List[str] | None = None, limit: int = 5) -> List[Experience]:
        wanted = set(symptoms or [])
        ranked = []
        for case in self._cases.values():
            score = (1.0 if case.problem == problem else 0.0) + 0.25 * len(wanted.intersection(case.symptoms))
            if score > 0:
                ranked.append((score, case))
        ranked.sort(key=lambda item: (item[0], item[1].confidence), reverse=True)
        return [case for _, case in ranked[:limit]]

    def successful(self, problem: str, symptoms: List[str] | None = None, limit: int = 5) -> List[Experience]:
        return [c for c in self.similar(problem, symptoms, limit * 2) if c.success is True][:limit]

    def failed(self, problem: str, symptoms: List[str] | None = None, limit: int = 5) -> List[Experience]:
        return [c for c in self.similar(problem, symptoms, limit * 2) if c.success is False][:limit]

    def snapshot(self) -> List[Dict[str, Any]]:
        return [c.__dict__.copy() for c in self._cases.values()]
