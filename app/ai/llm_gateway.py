"""Provider-neutral LLM gateway for Bitey.

The gateway is deliberately optional: Bitey keeps working with its deterministic
engine when no provider is configured. When a compatible chat-completions API is
configured, the model is used for language understanding, contextual replies and
structured intent extraction; business actions remain controlled by Bitey's core.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import httpx


SYSTEM_PROMPT = """You are Bitey, the conversational AI for BiteFixes.
Understand meaning, not exact spelling. Correct typos mentally and preserve
conversation context. Never invent business facts, prices, addresses, services,
ticket numbers or completed actions. Business data supplied in context is the
source of truth. Return ONLY valid JSON with keys:
intent, confidence, entities, user_goal, reply, needs_clarification.
intent must be a concise business intent such as mobile_repair, cctv_installation,
computer_repair, quote, greeting, or unknown. confidence is 0..1.
"""


def _endpoint() -> str:
    return (os.getenv("BITEY_LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")


def configured() -> bool:
    return bool(os.getenv("BITEY_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"))


def _model() -> str:
    return os.getenv("BITEY_LLM_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"


def understand(*, message: str, language: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Ask an LLM to understand a message, without granting it business authority."""
    if not configured():
        return {"used": False, "reason": "llm_not_configured"}
    api_key = os.getenv("BITEY_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    context = context or {}
    compact_context = {
        "language": language,
        "last_intent": context.get("last_intent"),
        "last_service": context.get("last_service"),
        "last_ticket": context.get("last_ticket"),
        "active_ticket": context.get("active_ticket"),
        "business_profile": context.get("business_profile"),
    }
    payload = {
        "model": _model(),
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({"message": message, "context": compact_context}, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
    }
    try:
        with httpx.Client(timeout=float(os.getenv("BITEY_LLM_TIMEOUT", "8"))) as client:
            response = client.post(f"{_endpoint()}/chat/completions", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content) if isinstance(content, str) else content
        if not isinstance(parsed, dict):
            raise ValueError("LLM returned a non-object response")
        parsed["used"] = True
        parsed["model"] = _model()
        return parsed
    except Exception as exc:
        return {"used": False, "reason": "llm_error", "error": str(exc)}
