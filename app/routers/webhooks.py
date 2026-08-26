"""Unified inbound channel adapters for Bitey, including WhatsApp Cloud API."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.services.bitey_gateway import handle_message, normalize_channel, SUPPORTED_CHANNELS
from app.services.outbound_channel_adapter import send_external_response

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _token(channel: str) -> str:
    return os.getenv(f"{channel.upper()}_WEBHOOK_TOKEN", "").strip()


def _company_id(channel: str) -> int:
    try:
        return max(1, int(os.getenv(f"{channel.upper()}_COMPANY_ID", os.getenv("BITEY_DEFAULT_COMPANY_ID", "1"))))
    except ValueError:
        return 1


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _verify_generic_token(channel: str, request: Request) -> None:
    expected = _token(channel)
    if not expected:
        if os.getenv("DEBUG", "false").lower() != "true":
            raise HTTPException(status_code=503, detail=f"{channel} webhook is not configured")
        return
    supplied = request.query_params.get("token") or request.headers.get("X-Webhook-Token", "")
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=403, detail="Invalid webhook token")


def _verify_whatsapp_signature(body: bytes, request: Request) -> None:
    secret = os.getenv("WHATSAPP_APP_SECRET", "").strip() or os.getenv("META_APP_SECRET", "").strip()
    if not secret:
        if os.getenv("DEBUG", "false").lower() != "true":
            raise HTTPException(status_code=503, detail="whatsapp app secret is not configured")
        return
    supplied = request.headers.get("X-Hub-Signature-256", "")
    if not supplied.startswith("sha256="):
        raise HTTPException(status_code=403, detail="Missing WhatsApp signature")
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=403, detail="Invalid WhatsApp signature")


def normalize_event(channel: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    if channel == "whatsapp":
        entry = (payload.get("entry") or [{}])[0]
        change = ((entry.get("changes") or [{}])[0]).get("value") or {}
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
        return {"message": text, "phone": phone, "email": "", "customer_name": _text(profile.get("name")), "last_name": "", "conversation_id": phone or _text(msg.get("id")), "channel": channel}
    if channel == "telegram":
        msg = payload.get("message") or payload.get("edited_message") or {}
        sender = msg.get("from") or {}
        text = _text(msg.get("text"))
        if not text:
            return None
        return {"message": text, "phone": "", "email": "", "customer_name": _text(sender.get("first_name")), "last_name": _text(sender.get("last_name")), "conversation_id": _text((msg.get("chat") or {}).get("id")), "channel": channel}
    if channel == "messenger":
        entry = (payload.get("entry") or [{}])[0]
        messaging = (entry.get("messaging") or [{}])[0]
        message = messaging.get("message") or {}
        text = _text(message.get("text"))
        if not text:
            return None
        return {"message": text, "phone": "", "email": "", "customer_name": "", "last_name": "", "conversation_id": _text((messaging.get("sender") or {}).get("id")), "channel": channel}
    text = _text(payload.get("message") or payload.get("text") or payload.get("body"))
    if not text:
        return None
    return {"message": text, "phone": _text(payload.get("phone") or payload.get("from_phone")), "email": _text(payload.get("email") or payload.get("from_email")), "customer_name": _text(payload.get("name") or payload.get("customer_name")), "last_name": _text(payload.get("last_name") or payload.get("surname")), "conversation_id": _text(payload.get("conversation_id") or payload.get("id")), "channel": channel}


async def _handle(channel: str, request: Request):
    if channel == "whatsapp":
        body = await request.body()
        _verify_whatsapp_signature(body, request)
        payload = json.loads(body.decode("utf-8"))
    else:
        _verify_generic_token(channel, request)
        payload = await request.json()

    event = normalize_event(channel, payload)
    if not event:
        return {"status": "ignored", "channel": channel}

    result = handle_message(company_id=_company_id(channel), message=event["message"], phone=event["phone"], email=event.get("email", ""), customer_name=event["customer_name"] or "Customer", last_name=event.get("last_name", ""), channel=normalize_channel(channel), conversation_id=event["conversation_id"], language_preference="auto")
    delivery = await send_external_response(channel=channel, response=result.get("response", "") if isinstance(result, dict) else "", event={**event, "conversation_id": result.get("conversation_id") if isinstance(result, dict) else None, "customer_id": result.get("customer_id") if isinstance(result, dict) else None})
    return {"status": "processed", "channel": channel, "external_conversation_id": event["conversation_id"], "conversation_id": result.get("conversation_id"), "customer_id": result.get("customer_id"), "response": result.get("response"), "result": result, "delivery": delivery}


@router.get("/{channel}")
async def verify(channel: str, request: Request):
    if channel not in SUPPORTED_CHANNELS:
        raise HTTPException(status_code=404, detail="Unsupported channel")
    if channel == "whatsapp":
        mode = request.query_params.get("hub.mode", "")
        verify_token = request.query_params.get("hub.verify_token", "")
        challenge = request.query_params.get("hub.challenge", "")
        expected = _token("whatsapp")
        if mode == "subscribe" and expected and hmac.compare_digest(verify_token, expected):
            return PlainTextResponse(challenge, status_code=200)
        raise HTTPException(status_code=403, detail="Invalid WhatsApp verification token")
    _verify_generic_token(channel, request)
    challenge = request.query_params.get("hub.challenge") or request.query_params.get("challenge")
    return {"status": "ok", "challenge": challenge} if challenge else {"status": "ok", "channel": channel}


@router.post("/{channel}")
async def receive(channel: str, request: Request):
    if channel not in SUPPORTED_CHANNELS:
        raise HTTPException(status_code=404, detail="Unsupported channel")
    return await _handle(channel, request)
