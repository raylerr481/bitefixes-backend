"""Bounded, capability-aware multi-provider consultation.

External AIs are the reasoning authorities. Bitey supplies governed tools and
context; it does not claim cognitive authority over the external advisors.
"""
from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Sequence
from app.ai.runtime import build_ai_orchestrator


def _search_context(message: str, language: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Run the shared web tool only when the rector was granted web_search.

    The search itself is not learning and is not business authority. Results are
    returned to the external AI as evidence with provenance so it can reason
    over them. Persistent learning remains a separate evaluated step.
    """
    capabilities = set(context.get("capabilities") or ())
    if "web_search" not in capabilities:
        return {}
    try:
        from app.services.web_search_service import search_web
        query = str(context.get("search_query") or message).strip()
        if not query:
            return {}
        result = search_web(query=query, language=language or "en", limit=5)
        results = result.get("results") or []
        return {
            "web_search": {
                "requested": True,
                "provider": result.get("provider"),
                "fallback_used": bool(result.get("fallback_used")),
                "verified": False,
                "results": results,
            }
        }
    except Exception as exc:
        print(f"[AI COUNCIL SEARCH WARNING] error={type(exc).__name__}")
        return {"web_search": {"requested": True, "provider": None, "results": [], "error": type(exc).__name__}}


async def _ask_provider(spec: Any, message: str, language: str, context: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        print(f"[AI COUNCIL] provider={spec.name} status=requested capabilities={','.join(spec.capabilities)}")
        tool_context = _search_context(message, language, context) if "web_search" in context.get("capabilities", ()) else {}
        answer = await spec.provider.generate(message, context={**context, **tool_context, "language": language})
        if not answer:
            print(f"[AI COUNCIL] provider={spec.name} status=empty")
            return None
        return {
            "provider": spec.name,
            "answer": str(answer).strip(),
            "cost_class": spec.cost_class,
            "capabilities": list(spec.capabilities),
            "tool_use": {"web_search": bool(tool_context.get("web_search", {}).get("requested"))},
            "evidence": tool_context.get("web_search", {}).get("results", []),
        }
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
    if not providers:
        providers = registry.available("general_reasoning")
    providers = providers[:max_providers]
    if not providers:
        print("[AI COUNCIL] status=no_enabled_providers")
        return []
    print("[AI COUNCIL] providers=" + ",".join(spec.name for spec in providers))

    async def run() -> List[Dict[str, Any]]:
        return [result for result in await asyncio.gather(*[_ask_provider(spec, message, language, context) for spec in providers]) if result]

    try:
        return asyncio.run(run())
    except RuntimeError:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(run())).result()
    except Exception as exc:
        print("[AI COUNCIL] status=error error=" + type(exc).__name__)
        return []
