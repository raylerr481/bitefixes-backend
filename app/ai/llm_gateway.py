"""Provider-neutral LLM gateway for Bitey.

The LLM is a semantic assistant, never the authority for business actions.
Provider selection is environment-driven and supports Groq/OpenRouter through
OpenAI-compatible APIs, while preserving the deterministic Bitey Core path.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
import httpx

SYSTEM_PROMPT = """You are Bitey, the conversational AI for BiteFixes.
Understand meaning, typos, colloquial language and short follow-ups. Preserve
conversation context. Never invent business facts, prices, addresses, services,
ticket numbers or completed actions. Business data supplied by Bitey Core is the
source of truth. Return ONLY valid JSON with keys:
intent, confidence, entities, user_goal, reply, needs_clarification.
intent must be a concise business intent such as mobile_repair, cctv_installation,
computer_repair, quote, greeting, or unknown. confidence is 0..1.
A greeting must be intent=greeting or unknown, never a service intent.
"""


def _provider_defaults() -> tuple[str, str, str]:
    # Explicit Bitey configuration always wins.
    if os.getenv("BITEY_LLM_API_KEY"):
        return (
            os.getenv("BITEY_LLM_BASE_URL", "https://api.openai.com/v1"),
            os.getenv("BITEY_LLM_MODEL", "gpt-4o-mini"),
            os.getenv("BITEY_LLM_API_KEY", ""),
        )
    # Groq is the preferred low-cost/free semantic provider already used by the
    # Bitey AI council.
    if os.getenv("GROQ_API_KEY"):
        return (
            os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            os.getenv("GROQ_API_KEY", ""),
        )
    if os.getenv("OPENROUTER_API_KEY"):
        return (
            os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
            os.getenv("OPENROUTER_API_KEY", ""),
        )
    if os.getenv("OPENAI_API_KEY"):
        return (
            os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            os.getenv("OPENAI_API_KEY", ""),
        )
    return "", "", ""


def configured() -> bool:
    return bool(_provider_defaults()[2])


def _endpoint() -> str:
    return _provider_defaults()[0].rstrip("/")


def _model() -> str:
    return _provider_defaults()[1]


def _provider_name() -> str:
    if os.getenv("BITEY_LLM_API_KEY"):
        return "bitey-configured"
    if os.getenv("GROQ_API_KEY"):
        return "groq"
    if os.getenv("OPENROUTER_API_KEY"):
        return "openrouter"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return "none"


def understand(*, message: str, language: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Use an available semantic provider without granting it business authority."""
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
        "history": (context.get("history") or [])[-6:],
    }
    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({"message": message, "context": compact_context}, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
    }
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
        if not isinstance(parsed, dict):
            raise ValueError("LLM returned a non-object response")
        parsed["used"] = True
        parsed["provider"] = _provider_name()
        parsed["model"] = model
        return parsed
    except Exception as exc:
        return {"used": False, "reason": "llm_error", "provider": _provider_name(), "error": str(exc)}
