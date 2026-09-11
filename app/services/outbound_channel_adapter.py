"""Common outbound adapter for every Bitey channel.

Transports the external AI final response without semantic rewriting.
"""
from __future__ import annotations
import os
from typing import Any
import httpx

class OutboundDeliveryError(RuntimeError):
    pass

def _env(channel: str, suffix: str, default: str = "") -> str:
    return os.getenv(f"{channel.upper()}_{suffix}", default).strip()

def _recipient(channel: str, event: dict[str, Any]) -> str:
    return str(event.get("external_conversation_id") or event.get("recipient_id") or event.get("phone") or "").strip()

def _url(channel: str) -> str:
    return _env(channel, "OUTBOUND_URL") or os.getenv("BITEY_OUTBOUND_URL", "").strip()

def _safe_recipient(recipient: str) -> str:
    value = str(recipient or "")
    if len(value) <= 4:
        return "***"
    return f"{value[:2]}***{value[-2:]}"

async def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=float(os.getenv("BITEY_OUTBOUND_TIMEOUT", "12"))) as client:
        response = await client.post(url, json=payload, headers=headers or {})
        if response.status_code >= 400:
            raise OutboundDeliveryError(f"provider_http_{response.status_code}")
        try:
            result = response.json()
            if isinstance(result, dict):
                return {**result, "http_status": response.status_code}
            return {"status": "sent", "http_status": response.status_code}
        except Exception:
            return {"status": "sent", "http_status": response.status_code}

async def send_external_response(*, channel: str, response: str, event: dict[str, Any]) -> dict[str, Any]:
    """Deliver the exact external-AI response; only transport JSON is built."""
    channel = str(channel or "api").strip().lower(); text = str(response or "").strip()
    if not text:
        print(f"[OUTBOUND] channel={channel} status=skipped reason=empty_response")
        return {"status": "skipped", "reason": "empty_response", "channel": channel}
    recipient = _recipient(channel, event)

    if channel == "telegram":
        token = _env(channel, "BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token or not recipient:
            print(f"[OUTBOUND] channel=telegram status=not_configured token={'yes' if token else 'no'} recipient={'yes' if recipient else 'no'}")
            return {"status": "not_configured", "channel": channel, "reason": "telegram_bot_token_or_recipient_missing"}
        print(f"[OUTBOUND] channel=telegram status=attempt recipient={_safe_recipient(recipient)} response_chars={len(text)}")
        try:
            result = await _post_json(f"https://api.telegram.org/bot{token}/sendMessage", {"chat_id": recipient, "text": text})
        except Exception as exc:
            print(f"[OUTBOUND] channel=telegram status=error recipient={_safe_recipient(recipient)} error={type(exc).__name__}")
            raise
        provider_ok = result.get("ok") if isinstance(result, dict) else None
        print(f"[OUTBOUND] channel=telegram status=provider_response recipient={_safe_recipient(recipient)} ok={provider_ok} http_status={result.get('http_status') if isinstance(result, dict) else None}")
        if provider_ok is False:
            description = str(result.get("description", "provider_rejected"))[:160]
            print(f"[OUTBOUND] channel=telegram status=rejected reason={description}")
            raise OutboundDeliveryError("telegram_provider_rejected")
        return {"status": "sent", "channel": channel, "provider": "telegram", "provider_result": result}

    if channel == "whatsapp":
        token = _env(channel, "ACCESS_TOKEN") or os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
        phone_id = _env(channel, "PHONE_NUMBER_ID") or os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
        graph_version = _env(channel, "GRAPH_API_VERSION", "v23.0") or "v23.0"
        if not token or not phone_id or not recipient:
            return {"status": "not_configured", "channel": channel, "reason": "whatsapp_credentials_or_recipient_missing"}
        result = await _post_json(
            f"https://graph.facebook.com/{graph_version}/{phone_id}/messages",
            {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"preview_url": False, "body": text},
            },
            {"Authorization": f"Bearer {token}"},
        )
        return {"status": "sent", "channel": channel, "provider": "whatsapp_cloud_api", "graph_api_version": graph_version, "provider_result": result}

    if channel == "messenger":
        token = _env(channel, "PAGE_ACCESS_TOKEN") or os.getenv("MESSENGER_PAGE_ACCESS_TOKEN", "").strip()
        if not token or not recipient: return {"status":"not_configured","channel":channel,"reason":"messenger_credentials_or_recipient_missing"}
        result = await _post_json("https://graph.facebook.com/v23.0/me/messages", {"recipient":{"id":recipient},"message":{"text":text},"messaging_type":"RESPONSE"}, {"Authorization":f"Bearer {token}"})
        return {"status":"sent","channel":channel,"provider":"messenger","provider_result":result}

    url = _url(channel)
    if not url: return {"status":"not_configured","channel":channel,"reason":"outbound_url_missing"}
    token = _env(channel, "OUTBOUND_TOKEN")
    headers = {"Authorization":f"Bearer {token}"} if token else {}
    result = await _post_json(url, {"channel":channel,"recipient":recipient,"external_conversation_id":event.get("external_conversation_id"),"conversation_id":event.get("conversation_id"),"customer_id":event.get("customer_id"),"message":text}, headers)
    return {"status":"sent","channel":channel,"provider":"custom","provider_result":result}
