"""Transport-only diagnostics for external AI providers.

External AI remains the cognitive authority. This module only verifies that a
provider can be reached and reports response structure. It never evaluates the
business quality of an answer and never decides which answer is better.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict

import httpx


def classify_http_status(status: int) -> str:
    return {
        400: "bad_request", 401: "authentication", 403: "forbidden",
        404: "endpoint_or_model", 408: "timeout", 409: "conflict",
        429: "rate_limit_or_quota", 500: "provider_error",
        502: "bad_gateway", 503: "provider_unavailable",
    }.get(status, "http_error")


def classify_exception(exc: Exception) -> Dict[str, Any]:
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if status is not None:
        return {"category": classify_http_status(int(status)), "http_status": int(status), "error_type": type(exc).__name__}
    if isinstance(exc, httpx.TimeoutException):
        return {"category": "timeout", "http_status": None, "error_type": type(exc).__name__}
    return {"category": type(exc).__name__, "http_status": None, "error_type": type(exc).__name__}


def extract_response_text(data: Any) -> str:
    """Normalize common provider response formats into one text value."""
    if data is None:
        return ""
    if isinstance(data, str):
        return data.strip()
    if isinstance(data, list):
        parts = [extract_response_text(item) for item in data]
        return "\n".join(part for part in parts if part).strip()
    if not isinstance(data, dict):
        for attr in ("output_text", "content", "text"):
            value = getattr(data, attr, None)
            if value:
                return extract_response_text(value)
        return ""
    if data.get("output_text"):
        return str(data["output_text"]).strip()
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        choice = choices[0] or {}
        if isinstance(choice, dict):
            message = choice.get("message") or {}
            if isinstance(message, dict) and message.get("content"):
                return extract_response_text(message["content"])
            if choice.get("text"):
                return extract_response_text(choice["text"])
    for key in ("content", "text", "response", "answer"):
        if data.get(key):
            return extract_response_text(data[key])
    output = data.get("output")
    if output:
        return extract_response_text(output)
    return ""


async def probe_openai_compatible(base_url: str, api_key: str, model: str, *, timeout: float = 20.0) -> Dict[str, Any]:
    """Check transport/HTTP/response structure only.

    A successful HTTP response is transport-healthy even when the probe has no
    visible text. Content availability is reported separately so a provider is
    not blocked from the real cognitive request by a false ``empty_response``.
    """
    started = time.perf_counter()
    normalized_base = base_url.rstrip("/")
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply only: OK"}],
        "max_tokens": 32,
        "temperature": 0,
    }
    if "api.groq.com" in normalized_base and model.startswith("openai/gpt-oss-"):
        payload["reasoning_effort"] = "low"
        payload["include_reasoning"] = False
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(normalized_base, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload)
        latency = round((time.perf_counter() - started) * 1000, 1)
        if response.is_success:
            try:
                data = response.json()
            except ValueError:
                data = response.text
            text = extract_response_text(data)
            keys = sorted(data.keys()) if isinstance(data, dict) else []
            return {
                "ok": True,
                "http_ok": True,
                "content_present": bool(text),
                "http_status": response.status_code,
                "category": "http_ok_with_content" if text else "http_ok_no_content",
                "latency_ms": latency,
                "response_format": type(data).__name__,
                "response_keys": keys[:20],
            }
        return {"ok": False, "http_ok": False, "content_present": False, "http_status": response.status_code, "category": classify_http_status(response.status_code), "latency_ms": latency, "response_content_type": response.headers.get("content-type", "")}
    except Exception as exc:
        result = classify_exception(exc)
        result.update({"ok": False, "http_ok": False, "content_present": False, "latency_ms": round((time.perf_counter() - started) * 1000, 1)})
        return result


async def probe_provider_spec(spec: Any) -> Dict[str, Any] | None:
    """Probe configured transport without granting cognitive authority."""
    provider = getattr(spec, "provider", spec)
    api_key = getattr(provider, "api_key", None)
    base_url = getattr(provider, "base_url", None)
    model = getattr(provider, "model", None)
    if not (api_key and base_url and model):
        endpoint = getattr(provider, "endpoint", None)
        credential_env = getattr(provider, "credential_env", "")
        model = getattr(provider, "model", None)
        if not endpoint or not model:
            return None
        api_key = os.getenv(str(credential_env), "") if credential_env else ""
        if credential_env and not api_key:
            return {"ok": False, "http_ok": False, "content_present": False, "category": "missing_credentials", "http_status": None, "latency_ms": 0.0}
        base_url = str(endpoint)
        if not base_url.endswith("/chat/completions"):
            base_url = base_url.rstrip("/") + "/chat/completions"
    else:
        base_url = f"{str(base_url).rstrip('/')}/chat/completions"
    return await probe_openai_compatible(base_url, str(api_key or ""), str(model))
