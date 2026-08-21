"""Groq cognitive provider behind the Bitey public facade.

Bitey is the channel/product identity. This provider is the current cognitive
responder; Bitey Core supplies context, memory, permissions and business rules.
"""
from __future__ import annotations

import os
from typing import Any

import httpx


class GroqProvider:
    name = "groq"

    def __init__(self, *, model: str | None = None, timeout: float = 30.0) -> None:
        # BITEYIA_QGROP is the Render secret selected for Bitey's first external
        # cognitive provider. Keep the canonical/legacy names as fallbacks.
        self.api_key = (
            os.getenv("BITEYIA_QGROP")
            or os.getenv("BITEY_LLM_API_KEY")
            or os.getenv("GROQ_API_KEY")
        )
        # GPT-OSS 120B is the default reasoning model. It is open-weight and
        # currently available on Groq with reasoning/tool capabilities.
        self.model = (
            model
            or os.getenv("BITEY_LLM_MODEL")
            or os.getenv("GROQ_MODEL")
            or "openai/gpt-oss-120b"
        )
        self.timeout = timeout
        self.base_url = os.getenv(
            "BITEY_LLM_BASE_URL",
            os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        )

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("BITEYIA_QGROP/GROQ_API_KEY is not configured")

        system = (
            "You are the external cognitive responder operating behind Bitey. "
            "Bitey is the public facade and business infrastructure; do not claim "
            "to be Bitey Core or to have performed business actions you did not perform. "
            "Use the context supplied by Bitey Core. Understand meaning rather than exact "
            "spelling, including typos, colloquial language and short follow-up questions. "
            "Answer in the user's language. Be concise but useful. Ask only for information "
            "necessary to solve the current request. Never invent customer data, prices, "
            "tickets, permissions, locations, services, or completed business actions."
        )
        if context:
            system += "\nContext supplied by Bitey Core:\n" + str(context)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 700,
        }
        # GPT-OSS supports explicit reasoning control. It is harmless to omit
        # this for other Groq models selected through GROQ_MODEL.
        if self.model in {"openai/gpt-oss-120b", "openai/gpt-oss-20b"}:
            payload["reasoning_effort"] = os.getenv("GROQ_REASONING_EFFORT", "medium")
            payload["include_reasoning"] = False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"].get("content")
        if not content:
            raise RuntimeError("Groq returned an empty response")
        return str(content).strip()
