"""Unified multi-channel webhook gateway for Bitey API."""
from __future__ import annotations
import hmac
import os
from fastapi import APIRouter, HTTPException, Request
from app.channels.registry import get_adapter, supported_channels
from app.services.bitey_gateway import handle_message, normalize_channel

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


async def _handle(channel: str, request: Request):
    _verify_token(channel, request)
    payload = await request.json()
    adapter = get_adapter(channel)
    if not adapter:
        raise HTTPException(status_code=404, detail="Channel adapter not installed")
    normalize_inbound, build_outbound = adapter
    company_id = int(request.query_params.get("company_id", "1"))
    event = normalize_inbound(payload, company_id=company_id)
    if not event:
        return {"status": "ignored", "channel": channel}
    req = event.request
    result = handle_message(
        company_id=req.company_id,
        message=req.message,
        phone=req.phone or "",
        email=req.email or "",
        customer_name=req.customer_name or "Customer",
        last_name=req.last_name or "",
        channel=normalize_channel(req.channel),
        conversation_id=req.conversation_id,
        language_preference=req.language_preference,
    )
    outbound = build_outbound({**result, "conversation_id": req.conversation_id})
    return {"status": "processed", "channel": channel, "conversation_id": req.conversation_id,
            "provider_message_id": event.provider_message_id, "delivery": "adapter_ready",
            "result": result, "outbound": outbound}


@router.get("/{channel}")
async def verify(channel: str, request: Request):
    if channel not in supported_channels():
        raise HTTPException(status_code=404, detail="Unsupported channel")
    _verify_token(channel, request)
    challenge = request.query_params.get("hub.challenge") or request.query_params.get("challenge")
    return {"status": "ok", "challenge": challenge} if challenge else {"status": "ok", "channel": channel}


@router.post("/{channel}")
async def receive(channel: str, request: Request):
    if channel not in supported_channels():
        raise HTTPException(status_code=404, detail="Unsupported channel")
    return await _handle(channel, request)
