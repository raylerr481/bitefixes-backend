"""Provider-agnostic AI gateway for Bitey.

Bitey Core remains authoritative for customers, services, workflows, tools,
permissions and tickets. External models may only assist with understanding
and response generation.

Provider priority:
1. OpenRouter free router (when explicitly enabled and keyed).
2. OpenAI (when explicitly enabled and keyed).

No provider is enabled by default.
"""

import os
from typing import Any, Dict, Optional

import httpx


class AIProvider:
    def __init__(self) -> None:
        self.openrouter_enabled = os.getenv("OPENROUTER_ENABLED", "false").lower() == "true"
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "openrouter/free")

        self.openai_enabled = os.getenv("OPENAI_ENABLED", "false").lower() == "true"
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

        self.timeout = float(os.getenv("AI_TIMEOUT", os.getenv("OPENAI_TIMEOUT", "20")))
        self.max_output_tokens = int(
            os.getenv("AI_MAX_OUTPUT_TOKENS", os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "500"))
        )

    def available(self) -> bool:
        return bool(
            (self.openrouter_enabled and self.openrouter_key)
            or (self.openai_enabled and self.openai_key)
        )

    @staticmethod
    def _context(system: str, context: Optional[Dict[str, Any]]) -> str:
        if not context:
            return system
        return (
            system
            + "\nBUSINESS CONTEXT (authoritative; never invent beyond it):\n"
            + str(context)
        )

    def _openai(self, system: str, user: str, context: Optional[Dict[str, Any]]) -> Optional[str]:
        if not (self.openai_enabled and self.openai_key):
            return None
        payload = {
            "model": self.openai_model,
            "input": [
                {"role": "system", "content": self._context(system, context)},
                {"role": "user", "content": user},
            ],
            "max_output_tokens": self.max_output_tokens,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    "https://api.openai.com/v1/responses",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                text = data.get("output_text")
                return text.strip() if isinstance(text, str) and text.strip() else None
        except Exception as exc:
            print("[AI PROVIDER WARNING][openai]", repr(exc))
            return None

    def _openrouter(self, system: str, user: str, context: Optional[Dict[str, Any]]) -> Optional[str]:
        if not (self.openrouter_enabled and self.openrouter_key):
            return None
        payload = {
            "model": self.openrouter_model,
            "input": [
                {"role": "system", "content": self._context(system, context)},
                {"role": "user", "content": user},
            ],
            "max_output_tokens": self.max_output_tokens,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    "https://openrouter.ai/api/v1/responses",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": os.getenv("BITEY_PUBLIC_URL", "https://bitefixes.com"),
                        "X-Title": "Bitey AI",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                text = data.get("output_text")
                if not text:
                    # Compatibility with OpenAI-style chat payloads returned by
                    # some OpenRouter routes.
                    choices = data.get("choices") or []
                    if choices:
                        text = ((choices[0].get("message") or {}).get("content"))
                return text.strip() if isinstance(text, str) and text.strip() else None
        except Exception as exc:
            print("[AI PROVIDER WARNING][openrouter]", repr(exc))
            return None

    def respond(self, system: str, user: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        # Prefer the free provider first. Paid OpenAI is only used when explicitly
        # enabled, and only if the free provider is unavailable or fails.
        text = self._openrouter(system, user, context)
        if text:
            return text
        return self._openai(system, user, context)


ai_provider = AIProvider()
