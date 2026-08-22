"""Runtime registry for Bitey channel adapters."""
from __future__ import annotations
from app.channels.telegram.handler import normalize_inbound as telegram_inbound, build_outbound as telegram_outbound
from app.channels.messenger.handler import normalize_inbound as messenger_inbound, build_outbound as messenger_outbound
from app.channels.whatsapp.handler import normalize_inbound as whatsapp_inbound, build_outbound as whatsapp_outbound

ADAPTERS = {
    "telegram": (telegram_inbound, telegram_outbound),
    "messenger": (messenger_inbound, messenger_outbound),
    "whatsapp": (whatsapp_inbound, whatsapp_outbound),
}


def get_adapter(channel: str):
    return ADAPTERS.get(channel)


def supported_channels() -> list[str]:
    return sorted(ADAPTERS)
