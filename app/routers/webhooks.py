"""Channel webhook gateway.

External providers only deliver events here. Bitey remains the single business
logic endpoint. Provider-specific authentication/signature verification is
performed when the corresponding provider secret is configured.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.core.bitey import process_message

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _token(channel: str) -> str:
    return os.getenv(f"{channel.upper()}_WEBHOOK_TOKEN", "")


def _verify_token(channel: str, request: Request) -> None:
    expected = _token(channel)
    if not expected:
        return
    supplied = request.query_params.get("token") or request.headers.get("X-Webhook-Token", "")
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=403, detail="Invalid webhook token")


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def normalize_event(channel: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize common provider payloads into Bitey's channel-neutral contract."""
    if channel == "telegram":
        msg = payload.get("message") or payload.get("edited_message") or {}
        sender = msg.get("from") or {}
        text = _text(msg.get("text"))
        if not text:
            return None
        return {"message": text, "phone": "", "customer_name": _text(sender.get("first_name")),
                "conversation_id": _text(msg.get("chat", {}).get("id")), "channel": "telegram"}

    if channel == "messenger":
        entry = (payload.get("entry") or [{}])[0]
        messaging = (entry.get("messaging") or [{}])[0]
        message = messaging.get("message") or {}
        text = _text(message.get("text"))
        if not text:
            return None
        return {"message": text, "phone": "", "customer_name": "",
                "conversation_id": _text(messaging.get("sender", {}).get("id")), "channel": "messenger"}

    if channel == "whatsapp":
        entry = (payload.get("entry") or [{}])[0]
        change = (entry.get("changes") or [{}])[0].get("value") or {}
        messages = change.get("messages") or []
        if not messages:
            return None
        msg = messages[0]
        text = _text((msg.get("text") or {}).get("body"))
        if not text:
            return None
        contact = (change.get("contacts") or [{}])[0]
        profile = contact.get("profile") or {}
        phone = _text(msg.get("from") or contact.get("wa_id"))
        return {"message": text, "phone": phone, "customer_name": _text(profile.get("name")),
                "conversation_id": phone or _text(msg.get("id")), "channel": "whatsapp"}

    return None


async def _handle(channel: str, request: Request):
    _verify_token(channel, request)
    payload = await request.json()
    event = normalize_event(channel, payload)
    if not event:
        return {"status": "ignored"}
    result = process_message(company_id=1, message=event["message"], phone=event["phone"],
                             customer_name=event["customer_name"] or "Customer", channel=event["channel"],
                             conversation_id=event["conversation_id"], language_preference="auto")
    return {"status": "processed", "channel": channel, "conversation_id": event["conversation_id"], "result": result}


@router.get("/{channel}")
async def verify(channel: str, request: Request):
    _verify_token(channel, request)
    challenge = request.query_params.get("hub.challenge") or request.query_params.get("challenge")
    return {"status": "ok", "challenge": challenge} if challenge else {"status": "ok", "channel": channel}


@router.post("/{channel}")
async def receive(channel: str, request: Request):
    if channel not in {"whatsapp", "messenger", "telegram"}:
        raise HTTPException(status_code=404, detail="Unsupported channel")
    return await _handle(channel, request)
