"""Structured problem state for multi-turn Bitey diagnosis.

This module is deliberately deterministic and provider-independent. It tracks
facts, symptoms, unknowns and hypotheses without allowing an LLM to mutate
production knowledge directly.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ProblemState:
    problem: str | None = None
    symptoms: List[str] = field(default_factory=list)
    facts: Dict[str, Any] = field(default_factory=dict)
    unknowns: List[str] = field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    diagnostic_pending: bool = True


class ProblemAnalyzer:
    """Maintain structured diagnostic state across conversation turns."""

    def start(self, problem: str) -> ProblemState:
        return ProblemState(problem=problem, diagnostic_pending=True)

    def add_symptom(self, state: ProblemState, symptom: str, **facts: Any) -> ProblemState:
        if symptom and symptom not in state.symptoms:
            state.symptoms.append(symptom)
        state.facts.update({k: v for k, v in facts.items() if v is not None})
        return state

    def add_evidence(self, state: ProblemState, source: str, observation: str, supports: str | None = None) -> ProblemState:
        state.evidence.append({"source": source, "observation": observation, "supports": supports})
        return state

    def add_hypothesis(self, state: ProblemState, name: str, confidence: float, reason: str = "") -> ProblemState:
        state.hypotheses.append({"name": name, "confidence": max(0.0, min(1.0, confidence)), "reason": reason})
        state.hypotheses.sort(key=lambda x: x["confidence"], reverse=True)
        state.confidence = state.hypotheses[0]["confidence"] if state.hypotheses else 0.0
        return state

    def unresolved(self, state: ProblemState) -> bool:
        return state.diagnostic_pending or bool(state.unknowns)

    def snapshot(self, state: ProblemState) -> Dict[str, Any]:
        return {
            "problem": state.problem,
            "symptoms": list(state.symptoms),
            "facts": dict(state.facts),
            "unknowns": list(state.unknowns),
            "hypotheses": list(state.hypotheses),
            "evidence": list(state.evidence),
            "confidence": state.confidence,
            "diagnostic_pending": state.diagnostic_pending,
        }
