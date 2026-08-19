"""Governed external-AI orchestration for Bitey.

No provider is called unless policy allows it and credentials are configured.
Providers are adapters; Bitey remains responsible for the final decision.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class AIAnswer:
    provider: str
    text: str
    confidence: float = 0.0
    source: str | None = None


class AIProvider(Protocol):
    name: str

    async def answer(self, question: str, context: dict[str, Any]) -> AIAnswer: ...


class CostGate:
    """Cheap deterministic policy before any paid/external call."""

    def allow(self, *, confidence: float, complexity: str, explicit_external: bool = False) -> bool:
        if os.getenv("AI_COUNCIL_ENABLED", "false").lower() != "true":
            return False
        if explicit_external:
            return True
        if complexity in {"technical_complex", "ambiguous", "knowledge_gap"}:
            return confidence < float(os.getenv("AI_LOCAL_CONFIDENCE_THRESHOLD", "0.80"))
        return False


class AICouncil:
    def __init__(self, providers: list[AIProvider] | None = None):
        self.providers = providers or []
        self.gate = CostGate()

    async def consult(
        self,
        question: str,
        context: dict[str, Any],
        *,
        local_confidence: float,
        complexity: str,
        explicit_external: bool = False,
    ) -> dict[str, Any]:
        if not self.gate.allow(confidence=local_confidence, complexity=complexity, explicit_external=explicit_external):
            return {"consulted": False, "reason": "local_resolution_or_policy"}

        answers: list[AIAnswer] = []
        for provider in self.providers:
            try:
                answers.append(await provider.answer(question, context))
            except Exception as exc:  # provider isolation: one failure must not break Bitey
                answers.append(AIAnswer(provider=getattr(provider, "name", "unknown"), text="", source=f"error:{type(exc).__name__}"))

        usable = [a for a in answers if a.text]
        agreement = round(sum(a.confidence for a in usable) / len(usable), 3) if usable else 0.0
        return {
            "consulted": bool(usable),
            "answers": [a.__dict__ for a in usable],
            "agreement_score": agreement,
            "learning_candidate": bool(usable),
        }
