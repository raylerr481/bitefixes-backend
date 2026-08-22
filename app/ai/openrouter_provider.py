"""Free OpenRouter cognitive providers for Bitey."""
from __future__ import annotations

import os
from typing import Any

import httpx

QWEN_FREE_MODEL = "qwen/qwen3-235b-a22b-instruct-2507:free"
DEEPSEEK_FREE_MODEL = "deepseek/deepseek-v4-flash:free"


def _extract_text(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None
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
    return None


class OpenRouterProvider:
    name = "openrouter-free"

    def __init__(self, *, model: str | None = None) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.model = (model or os.getenv("OPENROUTER_MODEL", QWEN_FREE_MODEL)).strip()
        self.timeout = float(os.getenv("AI_TIMEOUT", "20"))
        self.max_output_tokens = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "700"))
        self.free_only = os.getenv("OPENROUTER_FREE_ONLY", "true").lower() != "false"

    @staticmethod
    def is_free_model(model: str) -> bool:
        normalized = model.strip().lower()
        return normalized == "openrouter/free" or normalized.endswith(":free")

    @property
    def enabled(self) -> bool:
        return (
            os.getenv("OPENROUTER_ENABLED", "true").lower() != "false"
            and bool(self.api_key)
            and (not self.free_only or self.is_free_model(self.model))
        )

    async def generate(self, prompt: str, *, context: dict[str, Any] | None = None) -> str | None:
        if not self.enabled:
            return None
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": (
                    "You are an external cognitive worker behind Bitey AI. "
                    "Bitey is the public facade and owns business infrastructure. "
                    "Review the supplied customer/business context carefully. "
                    "Produce the final user-facing answer directly. Never invent customer data, prices, tickets, "
                    "permissions, service IDs or completed actions. Never execute an action. "
                    "Answer in the user's language."
                )},
                {"role": "user", "content": f"Context: {context or {}}\n\nTask: {prompt}"},
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
        content = _extract_text(data)
        if not content:
            keys = sorted(data.keys()) if isinstance(data, dict) else type(data).__name__
            print(f"[OPENROUTER EMPTY] model={self.model} keys={keys}")
        return content
