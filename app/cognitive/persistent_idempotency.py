"""Persistence contract for cross-process message idempotency."""
from __future__ import annotations

import hashlib
from typing import Any

from app.supabase_client import supabase


def request_fingerprint(scope_key: str, message: str) -> str:
    return hashlib.sha256(f"{scope_key}|{message.strip()}".encode("utf-8")).hexdigest()


def claim_message(*, company_id: int, channel: str, conversation_id: str, user_id: str | None, external_message_id: str, fingerprint: str) -> dict[str, Any] | None:
    if not external_message_id:
        return None
    existing = supabase.table("bitey_message_idempotency").select("*").eq("company_id", company_id).eq("channel", channel).eq("external_message_id", external_message_id).limit(1).execute()
    rows = existing.data or []
    if rows:
        return rows[0]
    inserted = supabase.table("bitey_message_idempotency").insert({
        "company_id": company_id,
        "channel": channel,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "external_message_id": external_message_id,
        "request_fingerprint": fingerprint,
        "status": "processing",
    }).execute()
    return (inserted.data or [None])[0]


def complete_message(*, row_id: int, response: dict[str, Any]) -> None:
    supabase.table("bitey_message_idempotency").update({
        "response_json": response,
        "status": "completed",
        "completed_at": "now()",
    }).eq("id", row_id).execute()
