"""Tenant/channel/user identity scope for portable Bitey deployments.

Business logic must never identify a conversation by message text alone.
The scope isolates company, channel, conversation and user identities while
keeping provider-specific IDs optional and opaque.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class IdentityScope:
    company_id: int
    channel: str
    conversation_id: str
    user_id: Optional[str] = None
    external_message_id: Optional[str] = None
    channel_user_id: Optional[str] = None

    def key(self) -> str:
        parts = [
            str(self.company_id),
            self.channel.strip().lower(),
            self.conversation_id.strip(),
            (self.user_id or "").strip(),
            (self.channel_user_id or "").strip(),
        ]
        return "identity:" + hashlib.sha256("|".join(parts).encode()).hexdigest()

    def message_key(self, message: str) -> str:
        external = (self.external_message_id or "").strip()
        if external:
            return f"message:{self.key()}:{external}"
        raw = f"{self.key()}|{message.strip()}"
        return "message:" + hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)
