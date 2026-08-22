"""Runtime provider diagnostics. No secrets are returned or persisted here."""
from __future__ import annotations
import time
from typing import Any, Dict
import httpx


def classify_http_status(status: int) -> str:
    return {400: "bad_request", 401: "authentication", 403: "forbidden", 404: "endpoint_or_model", 408: "timeout", 409: "conflict", 429: "rate_limit_or_quota", 500: "provider_error", 502: "bad_gateway", 503: "provider_unavailable"}.get(status, "http_error")

async def probe_openai_compatible(base_url: str, api_key: str, model: str, *, timeout: float = 20.0) -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(base_url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": model, "messages": [{"role": "user", "content": "Reply only: OK"}], "max_tokens": 8, "temperature": 0})
        latency = round((time.perf_counter() - started) * 1000, 1)
        if response.is_success:
            data = response.json(); text = str((data.get("choices") or [{}])[0].get("message", {}).get("content", ""))
            return {"ok": bool(text.strip()), "http_status": response.status_code, "category": "healthy" if text.strip() else "empty_response", "latency_ms": latency, "model": data.get("model", model)}
        return {"ok": False, "http_status": response.status_code, "category": classify_http_status(response.status_code), "latency_ms": latency, "provider_error": response.text[:500]}
    except httpx.TimeoutException:
        return {"ok": False, "http_status": None, "category": "timeout", "latency_ms": round((time.perf_counter() - started) * 1000, 1)}
    except Exception as exc:
        return {"ok": False, "http_status": None, "category": type(exc).__name__, "latency_ms": round((time.perf_counter() - started) * 1000, 1), "provider_error": str(exc)[:500]}
