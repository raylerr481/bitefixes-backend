"""Free OpenRouter cognitive provider for Bitey.

OpenRouter is an optional second cognitive source. Bitey Core remains the
facade and authority; this provider only proposes answers.
"""
import os
from typing import Any
import httpx

# Strong free reasoning choice currently available in OpenRouter.
# Keep this configurable so the router can be upgraded without code changes.
FREE_ROUTER_MODEL = "qwen/qwen3-235b-a22b-instruct-2507:free"


class OpenRouterProvider:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.model = os.getenv("OPENROUTER_MODEL", FREE_ROUTER_MODEL).strip() or FREE_ROUTER_MODEL
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

    async def generate(self, prompt: str, *, context: dict[str, Any]) -> str | None:
        if not self.enabled or (self.free_only and not self.is_free_model(self.model)):
            return None
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a free external reasoning specialist behind Bitey AI. "
                        "Bitey is the public facade. Propose accurate, practical answers "
                        "using the supplied context. Never invent customer data, prices, "
                        "tickets, permissions or completed actions. Answer in the user's language."
                    ),
                },
                {"role": "user", "content": f"Context: {context}\n\nTask: {prompt}"},
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
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        choices = data.get("choices") or []
        content = choices[0].get("message", {}).get("content") if choices else None
        return str(content).strip() if content else None
