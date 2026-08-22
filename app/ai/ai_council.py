"""Bounded external-AI council for Bitey with health-aware failover."""
from __future__ import annotations
import asyncio, re
from typing import Any, Dict, List, Sequence
from app.ai.runtime import build_ai_orchestrator
from app.ai.contextual_resolution import resolve_context, contextual_directive
from app.ai.provider_health import probe_provider_spec, classify_exception

RECTOR_DIRECTIVES = """
You are the external rector AI working inside a specific company context.
You are the primary reasoning authority for the user's response. Bitey does not replace your reasoning with a fixed intent/template.
Analyze the user's actual need, conversation history, company context, service scope and available evidence before answering.
Adapt the response to the company you are working for; never answer as a generic public chatbot.
Treat company services, capabilities, scope, exclusions and knowledge as the authoritative business environment.
Prefer the most relevant company service or capability when the need matches it, but do not force a service match.
If the company context lacks a necessary fact, identify the information gap and use governed web_search when appropriate.
Web research is for external/current facts such as locations, postal codes, availability or facts not present in company context; do not search for a company service already defined in context.
Never invent services, prices, addresses, technicians, availability, policies or technical facts.
Do not create or imply a ticket merely because a service intent was detected.
Distinguish exploration, diagnosis, proposal and explicit commitment.
For exploration or diagnosis, ask the smallest useful next question and preserve conversational references.
Never restart a conversation when a short follow-up can be resolved from history.
Never answer with a generic service catalog unless the user asks for the catalog.
When a user describes a problem matching a company service, respond as that company's service assistant: explain what can be done and what still must be verified, rather than telling the user to search the web for the service.
Answer naturally in the user's language and remain inside the company's domain.
""".strip()

def _search_context(message: str, language: str, context: Dict[str, Any]) -> Dict[str, Any]:
    if "web_search" not in set(context.get("capabilities") or ()): return {}
    try:
        from app.services.web_search_service import search_web
        query=str(context.get("search_query") or "").strip()
        if not query:
            postal=re.search(r"\b\d{5}-?\d{3}\b",message); query=f"CEP {postal.group(0)} Brasil" if postal else message.strip()
        if not query: return {}
        result=search_web(query=query,language=language or "en",limit=5)
        return {"web_search":{"requested":True,"query":query,"provider":result.get("provider"),"fallback_used":bool(result.get("fallback_used")),"verified":bool(result.get("verified")),"results":result.get("results") or []}}
    except Exception as exc:
        print(f"[AI COUNCIL SEARCH WARNING] error={type(exc).__name__}"); return {"web_search":{"requested":True,"provider":None,"results":[],"error":type(exc).__name__}}

def _business_index(context: Dict[str, Any]) -> Dict[str, Any]:
    def names(items: List[Any]) -> List[str]:
        out=[]
        for item in items or []:
            value=item
            if isinstance(item,dict): value=item.get("name") or item.get("title") or item.get("slug") or item.get("service") or item.get("capability") or item.get("domain")
            if value: out.append(str(value))
        return out
    return {"company":context.get("company") or {},"profile":context.get("business_profile") or {},"domains":names(context.get("domains")),"services":names(context.get("services")),"capabilities":names(context.get("capabilities")),"ai_scope":context.get("ai_scope") or {},"knowledge_available":bool(context.get("knowledge"))}

async def _ask_provider(spec: Any, message: str, language: str, context: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        state=resolve_context(message=message,business_context=context.get("business_context") or {},memory=context.get("memory") or {},intent=context.get("intent") or {})
        directive=contextual_directive(state); tool_context=_search_context(message,language,context); business_index=_business_index(context.get("business_context") or {})
        enriched={**context,"business_context_index":business_index,"contextual_state":state,"contextual_directive":directive,**tool_context,"language":language,"rector_directives":RECTOR_DIRECTIVES}
        prompt=f"{RECTOR_DIRECTIVES}\n\nBUSINESS ENVIRONMENT INDEX:\n{business_index}\n\nCONTEXTUAL STATE:\n{state}\n\nGOVERNED TOOL RESULT:\n{tool_context}\n\nUSER MESSAGE:\n{message.strip()}"
        print(f"[AI COUNCIL] provider={spec.name} status=requested")
        answer=await spec.provider.generate(prompt,context=enriched)
        if not answer: return {"_error":{"category":"empty_response","http_status":None},"provider":spec.name}
        return {"provider":spec.name,"answer":str(answer).strip(),"cost_class":spec.cost_class,"capabilities":list(spec.capabilities),"tool_use":{"web_search":bool(tool_context.get("web_search",{}).get("requested"))},"evidence":tool_context.get("web_search",{}).get("results",[]),"search_query":tool_context.get("web_search",{}).get("query"),"search_verified":bool(tool_context.get("web_search",{}).get("verified")),"contextual_state":state,"business_context_index":business_index}
    except Exception as exc:
        diagnostic=classify_exception(exc); print(f"[AI COUNCIL] provider={spec.name} status=error category={diagnostic.get('category')} http_status={diagnostic.get('http_status')}"); return {"_error":diagnostic,"provider":spec.name}

def consult(message: str, *, language: str, context: Dict[str, Any], max_providers: int = 2, capabilities: Sequence[str] | None = None) -> List[Dict[str, Any]]:
    """Try providers by priority, health-check each, and fail over on failure."""
    if max_providers<=0: return []
    registry=build_ai_orchestrator().registry; requested=tuple(dict.fromkeys(capabilities or ("general_reasoning",)))
    providers=[]; seen=set()
    for capability in requested:
        for spec in registry.available(capability):
            if spec.name not in seen: providers.append(spec); seen.add(spec.name)
    if not providers: providers=registry.available("general_reasoning")
    if not providers: return []
    print("[AI COUNCIL] providers="+",".join(spec.name for spec in providers))

    async def run() -> List[Dict[str, Any]]:
        successful=[]
        for spec in providers:
            if len(successful)>=max_providers: break
            health=await probe_provider_spec(spec)
            if health is not None and not health.get("ok"):
                print(f"[AI COUNCIL] provider={spec.name} health=unhealthy category={health.get('category')} http_status={health.get('http_status')}")
                continue
            result=await _ask_provider(spec,message,language,context)
            if result and result.get("answer"):
                result["provider_health"]=health; successful.append(result)
        return successful
    try: return asyncio.run(run())
    except RuntimeError:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool: return pool.submit(lambda:asyncio.run(run())).result()
    except Exception as exc:
        print("[AI COUNCIL] status=error error="+type(exc).__name__); return []
