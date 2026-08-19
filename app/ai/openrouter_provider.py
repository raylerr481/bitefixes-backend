"""OpenRouter provider adapter for Bitey.

This adapter is advisory only. It returns model output; it has no business
workflow or tool execution authority.
"""
import os
from typing import Any

import httpx


class OpenRouterProvider:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.model = os.getenv("OPENROUTER_MODEL", "openrouter/free")
        self.timeout = float(os.getenv("AI_TIMEOUT", "20"))
        self.max_output_tokens = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "500"))

    @property
    def enabled(self) -> bool:
        return os.getenv("OPENROUTER_ENABLED", "false").lower() == "true" and bool(self.api_key)

    async def generate(self, prompt: str, *, context: dict[str, Any]) -> str | None:
        if not self.enabled:
            return None
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an advisory reasoning component of Bitey AI. "
                        "Do not create tickets, change customer data, execute tools, "
                        "invent business facts, prices, policies, or permissions. "
                        "Return concise reasoning useful to Bitey Core."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context: {context}\n\nTask: {prompt}",
                },
            ],
            "max_tokens": self.max_output_tokens,
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://bitefixes.com"),
            "X-Title": os.getenv("OPENROUTER_APP_NAME", "Bitey AI"),
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        choices = data.get("choices") or []
        if not choices:
            return None
        return choices[0].get("message", {}).get("content")
