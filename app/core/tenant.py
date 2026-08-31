"""Backward-compatible tenant presentation and channel configuration.

The existing BiteFixes deployment remains the pilot tenant. These helpers make
its public identity configurable for future SaaS tenants without replacing the
current FastAPI, Supabase or Render architecture.
"""
from __future__ import annotations

import os


CUSTOMER_CHANNELS = ("whatsapp", "telegram", "website")


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


def tenant_config() -> dict:
    """Return non-secret tenant presentation metadata.

    Secrets and authoritative tenant identity remain server-side. This config
    is presentation/routing metadata only and is safe for API status payloads.
    """
    return {
        "tenant_key": _env("TENANT_KEY", "bitefixes"),
        "company_name": _env("TENANT_DISPLAY_NAME", "BiteFixes"),
        "assistant_name": _env("TENANT_ASSISTANT_NAME", "Bitey"),
        "logo_url": _env("TENANT_LOGO_URL", ""),
        "customer_channels": list(CUSTOMER_CHANNELS),
        "white_label": _env("TENANT_WHITE_LABEL", "false").lower() in {"1", "true", "yes", "on"},
    }
