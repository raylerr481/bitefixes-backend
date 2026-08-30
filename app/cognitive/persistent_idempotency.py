"""Atomic persistence contract for cross-process message idempotency."""
from __future__ import annotations

import hashlib
from typing import Any

from app.supabase_client import supabase


def request_fingerprint(scope_key: str, message: str) -> str:
    return hashlib.sha256(f"{scope_key}|{message.strip()}".encode("utf-8")).hexdigest()


def claim_message(*, company_id: int, channel: str, conversation_id: str, user_id: str | None, external_message_id: str, fingerprint: str) -> dict[str, Any] | None:
    if not external_message_id:
        return None
    result = supabase.rpc("claim_bitey_message", {
        "p_company_id": company_id,
        "p_channel": channel,
        "p_conversation_id": conversation_id,
        "p_user_id": user_id,
        "p_external_message_id": external_message_id,
        "p_request_fingerprint": fingerprint,
    }).execute()
    rows = result.data or []
    return rows[0] if rows else None


def complete_message(*, row_id: int, response: dict[str, Any]) -> None:
    supabase.rpc("complete_bitey_message", {
        "p_row_id": row_id,
        "p_response_json": response,
    }).execute()
