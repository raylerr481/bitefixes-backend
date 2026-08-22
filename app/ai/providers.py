"""Optional AI providers for Bitey.

Bitey is the transport/context/memory layer. External providers are the
cognitive authority and return the final answer for the interaction.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class HTTPProvider:
    def __init__(self, name: str, base_url: str, api_key: str | None, model: str):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, *, context: dict[str, Any]) -> str:
        raise NotImplementedError


class OllamaProvider(HTTPProvider):
    async def generate(self, prompt: str, *, context: dict[str, Any]) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": settings.AI_MAX_OUTPUT_TOKENS},
        }
        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            return response.json().get("response", "")


class OpenAICompatibleProvider(HTTPProvider):
    """Adapter for OpenAI-compatible external inference routers."""

    async def generate(self, prompt: str, *, context: dict[str, Any]) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": settings.AI_MAX_OUTPUT_TOKENS,
        }
        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices") if isinstance(data, dict) else None
        if isinstance(choices, list) and choices:
            first = choices[0] or {}
            message = first.get("message") if isinstance(first, dict) else None
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
                if isinstance(content, list):
                    parts = []
                    for part in content:
                        if isinstance(part, dict) and isinstance(part.get("text"), str):
                            parts.append(part["text"])
                    if parts:
                        return "".join(parts).strip()
            text = first.get("text") if isinstance(first, dict) else None
            if isinstance(text, str) and text.strip():
                return text.strip()

        output_text = data.get("output_text") if isinstance(data, dict) else None
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()
        return ""


class GroqProvider(OpenAICompatibleProvider):
    pass


class GeminiProvider(HTTPProvider):
    async def generate(self, prompt: str, *, context: dict[str, Any]) -> str:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": settings.AI_MAX_OUTPUT_TOKENS},
        }
        params = {"key": self.api_key}
        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/v1beta/models/{self.model}:generateContent",
                params=params,
                json=payload,
            )
            response.raise_for_status()
            candidates = response.json().get("candidates", [])
            if not candidates:
                return ""
            return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")


class HuggingFaceProvider(OpenAICompatibleProvider):
    pass


def build_provider_registry():
    """Build providers from environment without requiring any API key."""
    from .registry import AIProviderRegistry, ProviderSpec

    registry = AIProviderRegistry()
    registry.register(
        ProviderSpec(
            "ollama",
            enabled=True,
            priority=10,
            cost_class="local-free",
            capabilities=("general_reasoning", "coding", "summarization"),
            provider=OllamaProvider("ollama", settings.OLLAMA_BASE_URL, None, settings.OLLAMA_MODEL),
        )
    )

    if settings.GEMINI_API_KEY:
        registry.register(
            ProviderSpec(
                "gemini",
                enabled=True,
                priority=20,
                cost_class="free-tier-or-paid",
                capabilities=("general_reasoning", "coding", "multilingual"),
                provider=GeminiProvider(
                    "gemini", "https://generativelanguage.googleapis.com", settings.GEMINI_API_KEY, settings.GEMINI_MODEL
                ),
            )
        )

    if settings.GROQ_API_KEY:
        registry.register(
            ProviderSpec(
                "groq",
                enabled=True,
                priority=30,
                cost_class="free-tier-or-paid",
                capabilities=("general_reasoning", "coding", "fast_inference"),
                provider=GroqProvider("groq", "https://api.groq.com/openai/v1", settings.GROQ_API_KEY, settings.GROQ_MODEL),
            )
        )

    if settings.HF_API_TOKEN:
        registry.register(
            ProviderSpec(
                "huggingface",
                enabled=True,
                priority=40,
                cost_class="free-tier-or-paid",
                capabilities=("general_reasoning", "coding", "multilingual"),
                provider=HuggingFaceProvider(
                    "huggingface",
                    "https://router.huggingface.co/v1",
                    settings.HF_API_TOKEN,
                    settings.HF_MODEL,
                ),
            )
        )

    return registry
