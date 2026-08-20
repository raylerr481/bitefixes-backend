"""Optional local Ollama provider for zero-cloud-cost AI inference."""
from __future__ import annotations

import os
from typing import Any

import httpx


class OllamaProvider:
    name = "ollama"

    def __init__(self, *, timeout: float = 60.0) -> None:
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return os.getenv("OLLAMA_ENABLED", "false").lower() == "true"

    async def generate(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        if not self.enabled:
            raise RuntimeError("Ollama is disabled")
        system = (
            "You are Bitey's local advisory AI. Answer in the requested language. "
            "Never invent business facts, customer data, prices, permissions, tickets, or actions."
        )
        if context:
            system += "\nGoverned context:\n" + str(context)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": str(prompt)},
            ],
            "stream": False,
            "options": {"temperature": 0.2},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        text = ((data.get("message") or {}).get("content") or "").strip()
        if not text:
            raise RuntimeError("Ollama returned an empty response")
        return text
