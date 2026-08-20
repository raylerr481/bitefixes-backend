"""Groq provider for Bitey.

Supports the canonical Bitey LLM environment variables as well as the legacy
GROQ_* names. This keeps provider discovery and the LLM gateway aligned.
"""
from __future__ import annotations

import os
from typing import Any

import httpx


class GroqProvider:
    name = "groq"

    def __init__(self, *, model: str | None = None, timeout: float = 20.0) -> None:
        self.api_key = os.getenv("BITEY_LLM_API_KEY") or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("BITEY_LLM_MODEL") or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.timeout = timeout
        self.base_url = os.getenv("BITEY_LLM_BASE_URL") or os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("BITEY_LLM_API_KEY/GROQ_API_KEY is not configured")

        system = (
            "You are Bitey, an assistant for business service conversations. "
            "Understand meaning rather than exact spelling, including typos, "
            "colloquial language and short follow-up questions. Answer in the "
            "user's detected language. Preserve the supplied conversation context. "
            "Be concise but useful. Ask only for information necessary to complete "
            "the current workflow. Never invent customer data, prices, tickets, "
            "permissions, locations, services, or completed business actions."
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
            "max_tokens": 500,
        }
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

        return data["choices"][0]["message"]["content"].strip()
