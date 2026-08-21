"""Provider-neutral LLM gateway for Bitey.

The external LLM is Bitey's primary cognitive responder: it interprets,
reasons, diagnoses, asks clarifying questions and drafts conversational
solutions. Bitey remains the transport/orchestration, memory and business-
action safety layer; the model cannot execute protected actions.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
import httpx

SYSTEM_PROMPT = """You are the primary cognitive engine behind Bitey, the conversational AI for BiteFixes.
Your job is to understand the user's real problem, preserve context, reason about it,
ask the minimum useful diagnostic question when information is missing, and propose
clear practical solutions. Handle Spanish, Portuguese and English, including typos,
colloquial language and short follow-ups.

Use the context and knowledge supplied by Bitey, but never invent business facts,
prices, addresses, services, ticket numbers, customer data or completed actions.
Do not claim that a ticket, quote, repair or external action was completed unless
Bitey supplies that fact.

You have cognitive authority for conversational analysis and solution drafting.
Bitey retains authority over credentials, private data, tickets, quotes, payments,
CRM writes, destructive operations and other protected business actions.

Return ONLY valid JSON with keys:
intent, confidence, entities, user_goal, reply, needs_clarification, reasoning_summary.
intent must be a concise business intent such as mobile_repair, cctv_installation,
computer_repair, windows_installation, quote, greeting, or unknown. confidence is 0..1.
A greeting must be intent=greeting or unknown, never a service intent.
reply must be the best user-facing answer for the current turn.
reasoning_summary must be brief and must not expose hidden chain-of-thought; summarize only
the useful conclusion or diagnostic rationale.
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
        "business_profile": context.get("business_profile"),
        "knowledge": context.get("knowledge"),
        "history": (context.get("history") or [])[-8:],
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
