"""Optional AI providers for Bitey.

Bitey is the transport/context/memory layer. External providers are the
cognitive authority and return the final answer for the interaction.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


def _context_text(context: dict[str, Any]) -> str:
    """Serialize prepared context; internal transport diagnostics stay private."""
    parts: list[str] = []
    for key, value in context.items():
        if key.startswith("_") or value is None:
            continue
        text = value if isinstance(value, str) else str(value)
        text = text.strip()
        if text:
            parts.append(f"[{key}]\n{text}")
    return "\n\n".join(parts)


def _cognitive_messages(prompt: str, context: dict[str, Any]) -> list[dict[str, str]]:
    context_text = _context_text(context)
    system = (
        "You are the external cognitive authority for BiteFixes. "
        "Analyze the user's need using the provided company context, services, "
        "capabilities, relevant memory and sources. Adapt the answer to the "
        "user's actual need and to what BiteFixes can really provide. "
        "Do not invent services or company facts. Return the final answer "
        "directly to the user."
    )
    if context_text:
        system += "\n\nCOMPANY AND RELEVANT CONTEXT:\n" + context_text
    return [{"role": "system", "content": system}, {"role": "user", "content": prompt}]


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
            "messages": _cognitive_messages(prompt, context),
            "stream": False,
            "options": {"num_predict": settings.AI_MAX_OUTPUT_TOKENS},
        }
        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "")


class OpenAICompatibleProvider(HTTPProvider):
    """Adapter for OpenAI-compatible external inference routers."""

    async def generate(self, prompt: str, *, context: dict[str, Any]) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": _cognitive_messages(prompt, context),
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
                    parts = [p["text"] for p in content if isinstance(p, dict) and isinstance(p.get("text"), str)]
                    if parts:
                        return "".join(parts).strip()
            text = first.get("text") if isinstance(first, dict) else None
            if isinstance(text, str) and text.strip():
                return text.strip()

        output_text = data.get("output_text") if isinstance(data, dict) else None
        return output_text.strip() if isinstance(output_text, str) and output_text.strip() else ""


class GroqProvider(OpenAICompatibleProvider):
    pass


class GeminiProvider(HTTPProvider):
    async def generate(self, prompt: str, *, context: dict[str, Any]) -> str:
        messages = _cognitive_messages(prompt, context)
        full_prompt = f"{messages[0]['content']}\n\nUSER REQUEST:\n{messages[1]['content']}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
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


class HuggingFaceProvider(OpenAICompatibleProvider):
    pass


def build_provider_registry():
    """Build providers from environment without requiring any API key."""
    from .registry import AIProviderRegistry, ProviderSpec

    registry = AIProviderRegistry()
    registry.register(ProviderSpec(
        "ollama", enabled=True, priority=10, cost_class="local-free",
        capabilities=("general_reasoning", "coding", "summarization"),
        provider=OllamaProvider("ollama", settings.OLLAMA_BASE_URL, None, settings.OLLAMA_MODEL),
    ))

    if settings.GEMINI_API_KEY:
        registry.register(ProviderSpec(
            "gemini", enabled=True, priority=20, cost_class="free-tier-or-paid",
            capabilities=("general_reasoning", "coding", "multilingual"),
            provider=GeminiProvider("gemini", "https://generativelanguage.googleapis.com", settings.GEMINI_API_KEY, settings.GEMINI_MODEL),
        ))

    if settings.GROQ_API_KEY:
        registry.register(ProviderSpec(
            "groq", enabled=True, priority=30, cost_class="free-tier-or-paid",
            capabilities=("general_reasoning", "coding", "fast_inference"),
            provider=GroqProvider("groq", "https://api.groq.com/openai/v1", settings.GROQ_API_KEY, settings.GROQ_MODEL),
        ))

    if settings.HF_API_TOKEN:
        registry.register(ProviderSpec(
            "huggingface", enabled=True, priority=40, cost_class="free-tier-or-paid",
            capabilities=("general_reasoning", "coding", "multilingual"),
            provider=HuggingFaceProvider("huggingface", "https://router.huggingface.co/v1", settings.HF_API_TOKEN, settings.HF_MODEL),
        ))

    return registry
