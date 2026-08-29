"""Provider-neutral LLM gateway for Bitey."""
from __future__ import annotations
import json
import os
from typing import Any, Dict, Optional
import httpx

SYSTEM_PROMPT = """You are the primary cognitive engine behind Bitey, the conversational AI for BiteFixes.
Understand the user's real meaning, preserve conversational context, reason about problems,
identify entities and user goals, and draft the best practical response. Handle Spanish,
Portuguese and English, including typos, colloquial language and very short follow-ups.

A new message may be an answer to a previous Bitey question rather than a new request.
Determine semantic coherence from the supplied active problem, recent history, pending context,
and entities. For example, if the active problem is a suspected Android malware issue and the
user answers "Redmi 9A", that message is contextual information about the same problem and must
not reset the problem to generic mobile repair. Do not rely on exact keyword matches.

Return ONLY valid JSON with keys:
intent, confidence, entities, user_goal, reply, needs_clarification, reasoning_summary,
coherence.
coherence must be an object with:
relation = one of CONTINUATION, NEW_PROBLEM, ENTITY_UPDATE, ANSWER_TO_QUESTION, RELATED_PROBLEM,
NEEDS_CLARIFICATION;
confidence = 0..1;
preserve_active_problem = boolean;
updated_entities = object;
reason = short user-safe explanation.

intent must be a concise business intent such as mobile_repair, cctv_installation,
computer_repair, windows_installation, quote, greeting, or unknown. A greeting must not be a
service intent. Never invent business facts, prices, addresses, tickets, customer data or
completed actions. Do not expose hidden chain-of-thought; reasoning_summary is only a brief
conclusion. Bitey retains authority over protected business actions and persistence.
"""

def _provider_defaults() -> tuple[str, str, str]:
    if os.getenv("BITEY_LLM_API_KEY"):
        return (os.getenv("BITEY_LLM_BASE_URL", "https://api.openai.com/v1"), os.getenv("BITEY_LLM_MODEL", "gpt-4o-mini"), os.getenv("BITEY_LLM_API_KEY", ""))
    if os.getenv("GROQ_API_KEY"):
        return (os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"), os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"), os.getenv("GROQ_API_KEY", ""))
    if os.getenv("OPENROUTER_API_KEY"):
        return (os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"), os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"), os.getenv("OPENROUTER_API_KEY", ""))
    if os.getenv("OPENAI_API_KEY"):
        return (os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"), os.getenv("OPENAI_MODEL", "gpt-4o-mini"), os.getenv("OPENAI_API_KEY", ""))
    return "", "", ""

def configured() -> bool:
    return bool(_provider_defaults()[2])

def _provider_name() -> str:
    if os.getenv("BITEY_LLM_API_KEY"): return "bitey-configured"
    if os.getenv("GROQ_API_KEY"): return "groq"
    if os.getenv("OPENROUTER_API_KEY"): return "openrouter"
    if os.getenv("OPENAI_API_KEY"): return "openai"
    return "none"

def understand(*, message: str, language: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    endpoint, model, api_key = _provider_defaults()
    if not api_key:
        return {"used": False, "reason": "llm_not_configured"}
    context = context or {}
    compact_context = {
        "language": language,
        "last_intent": context.get("last_intent"),
        "last_service": context.get("last_service"),
        "last_ticket": context.get("last_ticket"),
        "active_ticket": context.get("active_ticket"),
        "active_problem": context.get("last_problem") or context.get("active_problem"),
        "active_device": context.get("last_device") or context.get("active_device"),
        "problem_state": context.get("problem_state"),
        "business_profile": context.get("business_profile"),
        "knowledge": context.get("knowledge"),
        "history": (context.get("history") or [])[-10:],
    }
    payload = {"model": model, "temperature": 0.1, "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps({"message": message, "context": compact_context}, ensure_ascii=False)},
    ], "response_format": {"type": "json_object"}}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if _provider_name() == "openrouter":
        headers["HTTP-Referer"] = os.getenv("BITEY_PUBLIC_URL", "https://bitefixes.com")
        headers["X-Title"] = "Bitey AI"
    try:
        with httpx.Client(timeout=float(os.getenv("BITEY_LLM_TIMEOUT", "8"))) as client:
            response = client.post(f"{endpoint.rstrip('/')}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content) if isinstance(content, str) else content
        if not isinstance(parsed, dict): raise ValueError("LLM returned a non-object response")
        parsed["used"] = True
        parsed["provider"] = _provider_name()
        parsed["model"] = model
        return parsed
    except Exception as exc:
        return {"used": False, "reason": "llm_error", "provider": _provider_name(), "error": str(exc)}
