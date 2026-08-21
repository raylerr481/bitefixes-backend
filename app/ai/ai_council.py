"""Bounded external-AI council for Bitey V30.

External AIs are the reasoning authorities. Bitey supplies company context,
conversation memory, governed tools and contextual-resolution state.
"""
from __future__ import annotations
import asyncio
import re
from typing import Any, Dict, List, Sequence
from app.ai.runtime import build_ai_orchestrator
from app.ai.contextual_resolution import resolve_context, contextual_directive

RECTOR_DIRECTIVES = """
You are the external rector AI working inside a specific company context.
Reason about the user's actual need before proposing an action.
Use the supplied business context, services, memory and evidence.
Do not invent services, prices, addresses, technicians or availability.
If an external fact is necessary, use the governed web_search capability.
Do not create or imply a ticket merely because a service intent was detected.
Distinguish exploration, diagnosis, proposal and explicit commitment.
For exploration or diagnosis, ask the smallest useful next question.
Never restart a conversation when a short follow-up can be resolved from history.
Never answer with a generic service catalog unless the user asks for the catalog.
Answer naturally in the user's language and remain inside the company's domain.
""".strip()


def _search_context(message: str, language: str, context: Dict[str, Any]) -> Dict[str, Any]:
    capabilities = set(context.get("capabilities") or ())
    if "web_search" not in capabilities: return {}
    try:
        from app.services.web_search_service import search_web
        query = str(context.get("search_query") or "").strip()
        if not query:
            postal = re.search(r"\b\d{5}-?\d{3}\b", message)
            query = f"CEP {postal.group(0)} Brasil" if postal else message.strip()
        if not query: return {}
        result = search_web(query=query, language=language or "en", limit=5)
        return {"web_search": {"requested": True, "query": query, "provider": result.get("provider"),
                               "fallback_used": bool(result.get("fallback_used")), "verified": bool(result.get("verified")),
                               "results": result.get("results") or []}}
    except Exception as exc:
        print(f"[AI COUNCIL SEARCH WARNING] error={type(exc).__name__}")
        return {"web_search": {"requested": True, "provider": None, "results": [], "error": type(exc).__name__}}


async def _ask_provider(spec: Any, message: str, language: str, context: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        state = resolve_context(message=message, business_context=context.get("business_context") or {},
                                memory=context.get("memory") or {}, intent=context.get("intent") or {})
        directive = contextual_directive(state)
        tool_context = _search_context(message, language, context)
        enriched_context = {**context, "contextual_state": state, "contextual_directive": directive,
                            **tool_context, "language": language, "rector_directives": RECTOR_DIRECTIVES}
        prompt = f"{RECTOR_DIRECTIVES}\n\n{directive}\n\nUSER MESSAGE:\n{message.strip()}"
        print(f"[AI COUNCIL] provider={spec.name} status=requested capabilities={','.join(spec.capabilities)}")
        answer = await spec.provider.generate(prompt, context=enriched_context)
        if not answer: return None
        return {"provider": spec.name, "answer": str(answer).strip(), "cost_class": spec.cost_class,
                "capabilities": list(spec.capabilities), "tool_use": {"web_search": bool(tool_context.get("web_search", {}).get("requested"))},
                "evidence": tool_context.get("web_search", {}).get("results", []),
                "search_query": tool_context.get("web_search", {}).get("query"),
                "search_verified": bool(tool_context.get("web_search", {}).get("verified")),
                "contextual_state": state}
    except Exception as exc:
        print(f"[AI COUNCIL] provider={spec.name} status=error error={type(exc).__name__}")
        return None


def consult(message: str, *, language: str, context: Dict[str, Any], max_providers: int = 2,
            capabilities: Sequence[str] | None = None) -> List[Dict[str, Any]]:
    if max_providers <= 0: return []
    registry = build_ai_orchestrator().registry
    requested = tuple(dict.fromkeys(capabilities or ("general_reasoning",)))
    providers, seen = [], set()
    for capability in requested:
        for spec in registry.available(capability):
            if spec.name not in seen: providers.append(spec); seen.add(spec.name)
    if not providers: providers = registry.available("general_reasoning")
    providers = providers[:max_providers]
    if not providers: return []
    print("[AI COUNCIL] providers=" + ",".join(spec.name for spec in providers))

    async def run() -> List[Dict[str, Any]]:
        return [result for result in await asyncio.gather(*[_ask_provider(spec, message, language, context) for spec in providers]) if result]
    try: return asyncio.run(run())
    except RuntimeError:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool: return pool.submit(lambda: asyncio.run(run())).result()
    except Exception as exc:
        print("[AI COUNCIL] status=error error=" + type(exc).__name__); return []
