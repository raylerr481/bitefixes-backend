"""Optional Google Gemini provider for Bitey's governed AI council.

The provider is advisory only. It never receives payment data, secrets, or
unauthorized tenant data from this module; callers are responsible for the
sanitized context contract.
"""
from __future__ import annotations

import os
from typing import Any

import httpx


class GeminiProvider:
    name = "gemini"

    def __init__(self, *, timeout: float = 20.0) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.timeout = timeout
        self.base_url = os.getenv(
            "GEMINI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/models",
        ).rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key) and os.getenv("GEMINI_ENABLED", "true").lower() != "false"

    async def generate(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        if not self.enabled:
            raise RuntimeError("Gemini is not configured")

        context_text = ""
        if context:
            context_text = "\nGoverned context (authoritative; do not invent facts):\n" + str(context)

        payload = {
            "system_instruction": {
                "parts": [{
                    "text": (
                        "You are Bitey's advisory AI. Answer in the requested language. "
                        "Never invent prices, customer data, permissions, tickets, or business actions. "
                        "Return useful reasoning for Bitey Core; Core remains authoritative."
                    )
                }]
            },
            "contents": [{"role": "user", "parts": [{"text": str(prompt) + context_text}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500},
        }
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        parts = (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
        text = "".join(str(part.get("text", "")) for part in parts).strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response")
        return text
