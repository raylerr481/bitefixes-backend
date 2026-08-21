"""Provider-agnostic, governed AI gateway for Bitey.

Bitey remains the public facade. External models provide the cognitive
response while this gateway governs context, limits, provider selection and
fallbacks.
"""
import os
from typing import Any, Dict, Optional

import httpx

from app.ai.policy import allow_call, max_message_chars, sanitize_context


class AIProvider:
    def __init__(self) -> None:
        self.groq_key = os.getenv("BITEYIA_QGROP", "").strip()
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        self.groq_enabled = os.getenv("GROQ_ENABLED", "true").lower() == "true"

        self.openrouter_enabled = os.getenv("OPENROUTER_ENABLED", "false").lower() == "true"
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "openrouter/free")

        self.openai_enabled = os.getenv("OPENAI_ENABLED", "false").lower() == "true"
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

        self.timeout = float(os.getenv("AI_TIMEOUT", "20"))
        self.max_output_tokens = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "500"))

    def available(self) -> bool:
        return bool(
            (self.groq_enabled and self.groq_key)
            or (self.openrouter_enabled and self.openrouter_key)
            or (self.openai_enabled and self.openai_key)
        )

    @staticmethod
    def _context(system: str, context: Optional[Dict[str, Any]]) -> str:
        safe = sanitize_context(context)
        return system + (
            "\nBUSINESS CONTEXT (authoritative; do not invent):\n" + str(safe)
            if safe
            else ""
        )

    def _request(
        self,
        url: str,
        key: str,
        model: str,
        system: str,
        user: str,
        context: Optional[Dict[str, Any]],
        headers: Optional[dict] = None,
    ) -> Optional[str]:
        if not allow_call():
            return None

        user = str(user or "")[:max_message_chars()]
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self._context(system, context)},
                {"role": "user", "content": user},
            ],
            "max_tokens": self.max_output_tokens,
        }

        request_headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        if headers:
            request_headers.update(headers)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=request_headers, json=payload)
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices") or []
                if choices:
                    text = (choices[0].get("message") or {}).get("content")
                    if isinstance(text, str) and text.strip():
                        return text.strip()
                return None
        except Exception as exc:
            print("[AI PROVIDER WARNING]", type(exc).__name__)
            return None

    def respond(
        self,
        system: str,
        user: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        # 1. Groq: primary external cognitive responder for the current phase.
        if self.groq_enabled and self.groq_key:
            text = self._request(
                "https://api.groq.com/openai/v1/chat/completions",
                self.groq_key,
                self.groq_model,
                system,
                user,
                context,
            )
            if text:
                return text

        # 2. OpenRouter: provider/model fallback.
        if self.openrouter_enabled and self.openrouter_key:
            text = self._request(
                "https://openrouter.ai/api/v1/chat/completions",
                self.openrouter_key,
                self.openrouter_model,
                system,
                user,
                context,
                {
                    "HTTP-Referer": os.getenv("BITEY_PUBLIC_URL", "https://bitefixes.com"),
                    "X-Title": "Bitey AI",
                },
            )
            if text:
                return text

        # 3. OpenAI: optional final fallback.
        if self.openai_enabled and self.openai_key:
            return self._request(
                "https://api.openai.com/v1/chat/completions",
                self.openai_key,
                self.openai_model,
                system,
                user,
                context,
            )

        return None

    def name(self) -> str:
        if self.groq_enabled and self.groq_key:
            return "groq"
        if self.openrouter_enabled and self.openrouter_key:
            return "openrouter"
        if self.openai_enabled and self.openai_key:
            return "openai"
        return "none"


ai_provider = AIProvider()
