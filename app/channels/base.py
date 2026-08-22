"""Channel adapter contracts for Bitey API.

Adapters translate provider payloads to the canonical Bitey message contract.
They do not contain business reasoning or AI authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.schemas.chat_schema import ChatRequest


@dataclass(frozen=True)
class InboundEvent:
    request: ChatRequest
    provider_message_id: str | None = None
    raw_event_type: str | None = None


class ChannelAdapter(Protocol):
    channel: str

    def verify(self, payload: dict[str, Any], headers: dict[str, str]) -> bool: ...
    def normalize(self, payload: dict[str, Any], *, company_id: int) -> InboundEvent | None: ...
    def build_outbound(self, response: dict[str, Any]) -> dict[str, Any]: ...
