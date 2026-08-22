"""Generic OpenAI-compatible provider for interchangeable open models.

Credentials are read only from environment variables. The database stores
provider/model metadata and a credential_env reference, never the secret.
"""
from __future__ import annotations

import os
from typing import Any

import httpx


def _extract_text(data: Any) -> str | None:
    """Extract text from common OpenAI-compatible response formats."""
    if not isinstance(data, dict):
        return None
    for key in ("output_text", "answer", "response"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    choices = data.get("choices") or []
    if choices and isinstance(choices[0], dict):
        choice = choices[0]
        message = choice.get("message") or {}
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text") or item.get("content")
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())
            if parts:
                return "\n".join(parts)
        text = choice.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()
    output = data.get("output")
    if isinstance(output, list):
        parts = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content") or []
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text") or block.get("content")
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())
        if parts:
            return "\n".join(parts)
    return None


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
            content = _extract_text(data)
            if not content:
                keys = sorted(data.keys()) if isinstance(data, dict) else type(data).__name__
                print(f"[OPEN-COMPATIBLE EMPTY] provider={self.name} model={self.model} keys={keys}")
            return content
        except Exception as exc:
            print(f"[OPEN-COMPATIBLE WARNING] {self.name}/{self.model}: {type(exc).__name__}")
            raise
