"""Safety gate for outbound channel delivery.

Default behavior is fail-closed: external messages are not sent unless a
channel is explicitly enabled in live mode. This keeps development/demo at
zero cost and prevents accidental provider calls.
"""
from __future__ import annotations
import os

SUPPORTED_CHANNELS = {"whatsapp", "telegram", "messenger"}


def channel_mode(channel: str) -> str:
    channel = str(channel or "").strip().lower()
    return os.getenv(f"{channel.upper()}_MODE", "mock").strip().lower() or "mock"


def live_enabled(channel: str) -> bool:
    channel = str(channel or "").strip().lower()
    explicit = os.getenv(f"{channel.upper()}_LIVE", "false").strip().lower() == "true"
    return channel in SUPPORTED_CHANNELS and explicit and channel_mode(channel) == "live"


def delivery_decision(channel: str) -> dict[str, object]:
    channel = str(channel or "").strip().lower()
    if channel not in SUPPORTED_CHANNELS:
        return {"allowed": True, "mode": "custom", "reason": "non_managed_channel"}
    if live_enabled(channel):
        return {"allowed": True, "mode": "live", "reason": "explicit_live_enablement"}
    return {"allowed": False, "mode": channel_mode(channel), "reason": "zero_cost_fail_closed"}
