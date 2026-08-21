"""Bounded, capability-aware multi-provider consultation.

Bitey is an apprentice during this stage. External providers are cognitive
workers and trainers: they can reason, challenge and teach, but never receive
business-write authority. Bitey Core remains the validation boundary.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Sequence

from app.ai.apprentice import provider_role
from app.ai.runtime import build_ai_orchestrator


async def _ask_provider(
    spec: Any,
    message: str,
    language: str,
    context: Dict[str, Any],
) -> Dict[str, Any] | None:
    try:
        worker_context = {
            **context,
            "language": language,
            "learning_mode": "apprentice",
            "bitey_status": "student",
            "provider_role": provider_role(spec.name),
            "write_policy": "providers_propose_bitey_validates",
        }
        print(
            f"[AI COUNCIL] provider={spec.name} role={provider_role(spec.name)} "
            f"status=requested capabilities={','.join(spec.capabilities)}"
        )
        answer = await spec.provider.generate(message, context=worker_context)
        if not answer:
            print(f"[AI COUNCIL] provider={spec.name} status=empty")
            return None
        return {
            "provider": spec.name,
            "role": provider_role(spec.name),
            "answer": str(answer).strip(),
            "cost_class": spec.cost_class,
            "capabilities": list(spec.capabilities),
            "authority": "advisory",
        }
    except Exception as exc:
        print(
            f"[AI COUNCIL] provider={spec.name} status=error "
            f"error={type(exc).__name__}"
        )
        return None


def consult(
    message: str,
    *,
    language: str,
    context: Dict[str, Any],
    max_providers: int = 2,
    capabilities: Sequence[str] | None = None,
) -> List[Dict[str, Any]]:
    """Consult free/approved providers as Bitey's temporary training council."""
    if max_providers <= 0:
        return []

    registry = build_ai_orchestrator().registry
    requested = tuple(dict.fromkeys(capabilities or ("general_reasoning",)))
    providers: list[Any] = []
    seen: set[str] = set()
    for capability in requested:
        for spec in registry.available(capability):
            if spec.name not in seen:
                providers.append(spec)
                seen.add(spec.name)

    if not providers:
        providers = registry.available("general_reasoning")
    providers = providers[:max_providers]
    if not providers:
        print("[AI COUNCIL] status=no_enabled_providers")
        return []

    print("[AI COUNCIL] providers=" + ",".join(spec.name for spec in providers))

    async def run() -> List[Dict[str, Any]]:
        results = await asyncio.gather(
            *[_ask_provider(spec, message, language, context) for spec in providers]
        )
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
