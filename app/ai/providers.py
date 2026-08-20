"""Optional AI providers for Bitey.

Ollama is the local/open-source default. Gemini, Groq and Hugging Face are
opt-in cloud adapters. They are advisory only: Bitey Core remains authoritative.
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
    async def generate(self, prompt: str, *, context: dict[str, Any]) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": settings.AI_MAX_OUTPUT_TOKENS,
        }
        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


class GeminiProvider(HTTPProvider):
    async def generate(self, prompt: str, *, context: dict[str, Any]) -> str:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": settings.AI_MAX_OUTPUT_TOKENS},
        }
        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{self.base_url}/v1beta/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json=payload,
            )
            response.raise_for_status()
            candidates = response.json().get("candidates", [])
            if not candidates:
                return ""
            return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")


def build_provider_registry():
    """Build only providers that are configured; no cloud key is mandatory."""
    from .registry import AIProviderRegistry, ProviderSpec

    registry = AIProviderRegistry()
    registry.register(
        ProviderSpec(
            "ollama", True, 10, "local-free",
            ("general_reasoning", "coding", "summarization"),
            OllamaProvider("ollama", settings.OLLAMA_BASE_URL, None, settings.OLLAMA_MODEL),
        )
    )

    if settings.GEMINI_API_KEY:
        registry.register(
            ProviderSpec(
                "gemini", True, 20, "free-tier-or-paid",
                ("general_reasoning", "coding", "multilingual"),
                GeminiProvider("gemini", "https://generativelanguage.googleapis.com", settings.GEMINI_API_KEY, settings.GEMINI_MODEL),
            )
        )

    if settings.GROQ_API_KEY:
        registry.register(
            ProviderSpec(
                "groq", True, 30, "free-tier-or-paid",
                ("general_reasoning", "coding", "fast_inference"),
                OpenAICompatibleProvider("groq", "https://api.groq.com/openai/v1", settings.GROQ_API_KEY, settings.GROQ_MODEL),
            )
        )

    if settings.HF_API_TOKEN:
        registry.register(
            ProviderSpec(
                "huggingface", True, 40, "free-tier-or-paid",
                ("general_reasoning", "coding", "multilingual"),
                OpenAICompatibleProvider("huggingface", "https://router.huggingface.co/v1", settings.HF_API_TOKEN, settings.HF_MODEL),
            )
        )

    return registry
