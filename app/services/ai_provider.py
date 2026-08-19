"""Provider-agnostic AI gateway for Bitey.

OpenAI is optional and disabled unless explicitly enabled. The provider only
returns structured reasoning text; Bitey Core remains authoritative for
customers, services, workflows, tools, permissions, and tickets.
"""

import os
from typing import Any, Dict, Optional

import httpx


class AIProvider:
    def __init__(self) -> None:
        self.enabled = os.getenv("OPENAI_ENABLED", "false").lower() == "true"
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
        self.timeout = float(os.getenv("OPENAI_TIMEOUT", "20"))
        self.max_output_tokens = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "500"))

    def available(self) -> bool:
        return self.enabled and bool(self.api_key)

    def respond(self, system: str, user: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if not self.available():
            return None

        context_text = ""
        if context:
            context_text = "\nBUSINESS CONTEXT (authoritative, do not invent beyond it):\n" + str(context)

        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": system + context_text},
                {"role": "user", "content": user},
            ],
            "max_output_tokens": self.max_output_tokens,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    "https://api.openai.com/v1/responses",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                text = data.get("output_text")
                return text.strip() if isinstance(text, str) and text.strip() else None
        except Exception as exc:
            print("[AI PROVIDER WARNING]", repr(exc))
            return None


ai_provider = AIProvider()
