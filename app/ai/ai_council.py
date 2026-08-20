"""Bounded, capability-aware multi-provider consultation.

Bitey wakes only the capabilities requested by its trigger plan. Providers are
advisors; Bitey Core remains the final evaluator and business authority.
"""
from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Sequence
from app.ai.runtime import build_ai_orchestrator

async def _ask_provider(spec: Any, message: str, language: str, context: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        print(f"[AI COUNCIL] provider={spec.name} status=requested capabilities={','.join(spec.capabilities)}")
        answer = await spec.provider.generate(message, context={**context, "language": language})
        if not answer:
            print(f"[AI COUNCIL] provider={spec.name} status=empty")
            return None
        return {"provider": spec.name, "answer": str(answer).strip(), "cost_class": spec.cost_class, "capabilities": list(spec.capabilities)}
    except Exception as exc:
        print(f"[AI COUNCIL] provider={spec.name} status=error error={type(exc).__name__}")
        return None


def consult(message: str, *, language: str, context: Dict[str, Any], max_providers: int = 2,
            capabilities: Sequence[str] | None = None) -> List[Dict[str, Any]]:
    if max_providers <= 0:
        return []
    registry = build_ai_orchestrator().registry
    requested = tuple(dict.fromkeys(capabilities or ("general_reasoning",)))
    providers: list[Any] = []
    seen: set[str] = set()
    for capability in requested:
        for spec in registry.available(capability):
            if spec.name not in seen:
                providers.append(spec); seen.add(spec.name)
    # Safe fallback: semantic/freshness triggers can still use general reasoning
    # when no specialized provider exists.
    if not providers:
        providers = registry.available("general_reasoning")
    providers = providers[:max_providers]
    if not providers:
        print("[AI COUNCIL] status=no_enabled_providers")
        return []
    print("[AI COUNCIL] providers=" + ",".join(spec.name for spec in providers))

    async def run() -> List[Dict[str, Any]]:
        results = await asyncio.gather(*[_ask_provider(spec, message, language, context) for spec in providers])
        return [result for result in results if result]

    try:
        return asyncio.run(run())
    except RuntimeError:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(run())).result()
    except Exception as exc:
        print("[AI COUNCIL] status=error error=" + type(exc).__name__)
        return []
