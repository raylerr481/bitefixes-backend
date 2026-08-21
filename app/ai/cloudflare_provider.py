"""Cloudflare Workers AI provider.

Used only as a zero-cost-eligible online model provider. Credentials are read
from environment variables and never returned to clients.
"""
from __future__ import annotations

import os
from typing import Any

import httpx


DEFAULT_MODEL = os.getenv("CLOUDFLARE_AI_MODEL", "@cf/qwen/qwen3-0.6b")


class CloudflareAIProvider:
    name = "cloudflare-free"

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
        self.model = model
        self.enabled = bool(self.account_id and self.api_token and os.getenv("CLOUDFLARE_AI_ENABLED", "true").lower() != "false")
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run" if self.account_id else ""

    async def generate(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        if not self.enabled:
            raise RuntimeError("Cloudflare Workers AI is not configured")
        payload = {"prompt": prompt}
        if context:
            payload["context"] = context
        headers = {"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(f"{self.base_url}/{self.model}", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        result = data.get("result") or {}
        return str(result.get("response") or result.get("text") or "").strip()
