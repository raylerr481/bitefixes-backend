"""Bitey external-AI orchestrator.

Bitey is the public facade. External models are cognitive workers that can
propose, challenge and improve answers, while Bitey Core keeps authority over
memory, customer data, permissions, workflows and business actions.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any

from .registry import AIProviderRegistry, ProviderSpec


class AIOrchestrator:
    def __init__(self, registry: AIProviderRegistry) -> None:
        self.registry = registry

    def choose(self, capability: str = "general_reasoning") -> ProviderSpec | None:
        providers = self.registry.available(capability)
        return providers[0] if providers else None

    async def ask(
        self,
        prompt: str,
        *,
        capability: str = "general_reasoning",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Fast path: use the highest-priority available cognitive provider."""
        spec = self.choose(capability)
        if not spec:
            return {"status": "no_provider", "answer": None, "provider": None}
        try:
            result = await spec.provider.generate(prompt, context=context or {})
            return {"status": "ok", "provider": spec.name, "answer": result}
        except Exception as exc:
            return {
                "status": "provider_error",
                "provider": spec.name,
                "answer": None,
                "error": type(exc).__name__,
            }

    async def ask_council(
        self,
        prompt: str,
        *,
        capability: str = "general_reasoning",
        context: dict[str, Any] | None = None,
        max_providers: int | None = None,
    ) -> dict[str, Any]:
        """Ask multiple external models and return the best usable candidate.

        The first provider is normally Groq. A free OpenRouter model is used as
        an independent challenger when configured. This is deliberately a
        bounded council: external models never receive tool authority.
        """
        providers = self.registry.available(capability)
        limit = max_providers or int(os.getenv("AI_COUNCIL_MAX_PROVIDERS", "2"))
        providers = providers[: max(1, limit)]
        if not providers:
            return {"status": "no_provider", "answer": None, "provider": None, "candidates": []}

        async def run(spec: ProviderSpec) -> dict[str, Any]:
            try:
                answer = await spec.provider.generate(prompt, context=context or {})
                return {"provider": spec.name, "answer": answer, "status": "ok" if answer else "empty"}
            except Exception as exc:
                return {"provider": spec.name, "answer": None, "status": "error", "error": type(exc).__name__}

        candidates = await asyncio.gather(*(run(spec) for spec in providers))
        usable = [c for c in candidates if c.get("answer")]
        if not usable:
            return {"status": "provider_error", "answer": None, "provider": None, "candidates": candidates}

        # Prefer the highest-priority usable model. The council's value is the
        # independent second opinion and telemetry, not an opaque model override.
        selected = usable[0]
        return {
            "status": "ok",
            "provider": selected["provider"],
            "answer": selected["answer"],
            "candidates": candidates,
            "council_used": len(usable) > 1,
        }
