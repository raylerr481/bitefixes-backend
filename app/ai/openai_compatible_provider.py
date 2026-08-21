"""Generic OpenAI-compatible provider for interchangeable open models.

Credentials are read only from environment variables. The database stores
provider/model metadata and a credential_env reference, never the secret.
"""
from __future__ import annotations

import os
from typing import Any

import httpx


class OpenAICompatibleProvider:
    def __init__(self, *, name: str, model: str, endpoint: str, credential_env: str = "", enabled: bool = True) -> None:
        self.name = name
        self.model = model
        self.endpoint = endpoint.rstrip("/")
        self.credential_env = credential_env.strip()
        self.config_enabled = enabled
        self.timeout = float(os.getenv("AI_TIMEOUT", "20"))
        self.max_output_tokens = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "700"))

    @property
    def enabled(self) -> bool:
        if not self.config_enabled or not self.endpoint:
            return False
        return not self.credential_env or bool(os.getenv(self.credential_env, "").strip())

    async def generate(self, prompt: str, *, context: dict[str, Any] | None = None) -> str | None:
        if not self.enabled:
            return None
        system = (
            "You are an external cognitive worker behind Bitey AI. "
            "Use the supplied company context and conversation context. "
            "Do not invent prices, addresses, technicians, availability, tickets or permissions. "
            "Do not execute actions. Answer in the user's language and ask the smallest useful "
            "next question when information is missing."
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"Context: {context or {}}\n\nTask: {prompt}"},
            ],
            "max_tokens": self.max_output_tokens,
            "temperature": 0.1,
        }
        headers = {"Content-Type": "application/json"}
        if self.credential_env:
            headers["Authorization"] = f"Bearer {os.getenv(self.credential_env, '').strip()}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.endpoint}/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
            choices = data.get("choices") or []
            content = choices[0].get("message", {}).get("content") if choices else None
            return str(content).strip() if content else None
        except Exception as exc:
            print(f"[OPEN-COMPATIBLE WARNING] {self.name}/{self.model}: {type(exc).__name__}")
            return None
