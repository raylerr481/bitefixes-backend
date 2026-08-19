"""Groq provider for Bitey.

Groq is optional. When GROQ_API_KEY is absent the provider stays disabled and
Bitey's deterministic core continues to work normally.
"""
from __future__ import annotations

import os
from typing import Any

import httpx


class GroqProvider:
    name = "groq"

    def __init__(self, *, model: str | None = None, timeout: float = 20.0) -> None:
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.timeout = timeout
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

        system = (
            "You are Bitey, an assistant for business service conversations. "
            "Answer in the user's detected language. Be concise. Ask only for "
            "information that is necessary to understand the need, register the "
            "customer, or complete the current workflow. Never invent customer "
            "data, prices, tickets, permissions, or business actions."
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
