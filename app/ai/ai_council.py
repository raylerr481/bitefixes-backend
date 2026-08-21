"""Bounded multi-provider consultation.

Bitey asks multiple enabled advisory providers when justified. External models
receive a protected, minimized context and remain advisory only.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from app.ai.privacy_engine import sanitize
from app.ai.runtime import build_ai_orchestrator
from app.ai.trust_engine import rank_candidates


async def _ask_provider(spec: Any, message: str, language: str, context: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        answer = await spec.provider.generate(
            sanitize(message),
            context={**sanitize(context), "language": language},
        )
        if not answer:
            return None
        return {
            "provider": spec.name,
            "answer": str(answer).strip(),
            "cost_class": spec.cost_class,
        }
    except Exception as exc:
        print("[AI COUNCIL WARNING]", spec.name, type(exc).__name__)
        return None


def consult(message: str, *, language: str, context: Dict[str, Any], max_providers: int = 2) -> List[Dict[str, Any]]:
    """Collect bounded independent advisory answers through the privacy boundary."""
    if max_providers <= 0:
        return []

    registry = build_ai_orchestrator().registry
    providers = registry.available("general_reasoning")[:max_providers]
    if not providers:
        return []

    safe_context = sanitize(context)

    async def run() -> List[Dict[str, Any]]:
        results = await asyncio.gather(
            *[_ask_provider(spec, message, language, safe_context) for spec in providers],
            return_exceptions=False,
        )
        return rank_candidates([result for result in results if result])

    try:
        return asyncio.run(run())
    except RuntimeError:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(run())).result()
    except Exception as exc:
        print("[AI COUNCIL WARNING]", type(exc).__name__)
        return []
