"""Governed AI orchestration facade for Bitey Core.

External models are advisory. Bitey Core remains authoritative for tenant
context, semantics, services, workflows, tools, tickets and persistence.
"""
from typing import Any, Dict

from app.ai.runtime import build_ai_orchestrator


def enrich(message: str, *, language: str, intent: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Ask one configured advisory model for semantic enrichment.

    The provider is selected by the same free/local-first registry used by the
    AI council, so Bitey no longer has a hidden OpenRouter/OpenAI-only path.
    """
    intent = intent or {}
    orchestrator = build_ai_orchestrator()
    spec = orchestrator.choose("semantic_analysis")
    if not spec:
        return {"used": False, "reason": "no_provider", "provider": None}

    system_context = {
        "language": language,
        "current_intent": intent.get("intent"),
        "current_confidence": intent.get("confidence", 0),
    }
    try:
        import asyncio

        async def run() -> Dict[str, Any]:
            result = await orchestrator.ask(
                message,
                capability="semantic_analysis",
                context=system_context,
            )
            return {
                "used": result.get("status") == "ok",
                "text": result.get("answer"),
                "provider": result.get("provider"),
                "status": result.get("status"),
            }

        try:
            return asyncio.run(run())
        except RuntimeError:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(lambda: asyncio.run(run())).result()
    except Exception as exc:
        return {"used": False, "reason": type(exc).__name__, "provider": spec.name}
