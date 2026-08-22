"""Runtime provider health and failure diagnostics. Secrets are never persisted."""
from __future__ import annotations
import os
import time
from typing import Any, Dict
import httpx


def classify_http_status(status: int) -> str:
    return {400:"bad_request",401:"authentication",403:"forbidden",404:"endpoint_or_model",408:"timeout",409:"conflict",429:"rate_limit_or_quota",500:"provider_error",502:"bad_gateway",503:"provider_unavailable"}.get(status,"http_error")


def classify_exception(exc: Exception) -> Dict[str, Any]:
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if status is not None:
        return {"category": classify_http_status(int(status)), "http_status": int(status), "error_type": type(exc).__name__}
    if isinstance(exc, httpx.TimeoutException):
        return {"category":"timeout", "http_status":None, "error_type":type(exc).__name__}
    return {"category":type(exc).__name__, "http_status":None, "error_type":type(exc).__name__}


async def probe_openai_compatible(base_url: str, api_key: str, model: str, *, timeout: float = 20.0) -> Dict[str, Any]:
    started=time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response=await client.post(base_url, headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"}, json={"model":model,"messages":[{"role":"user","content":"Reply only: OK"}],"max_tokens":8,"temperature":0})
        latency=round((time.perf_counter()-started)*1000,1)
        if response.is_success:
            data=response.json(); text=str((data.get("choices") or [{}])[0].get("message",{}).get("content","") or "")
            return {"ok":bool(text.strip()),"http_status":response.status_code,"category":"healthy" if text.strip() else "empty_response","latency_ms":latency}
        return {"ok":False,"http_status":response.status_code,"category":classify_http_status(response.status_code),"latency_ms":latency}
    except Exception as exc:
        result=classify_exception(exc); result["ok"]=False; result["latency_ms"]=round((time.perf_counter()-started)*1000,1); return result


async def probe_provider_spec(spec: Any) -> Dict[str, Any] | None:
    """Probe OpenAI-compatible providers using either explicit key/base_url or env-backed endpoint."""
    provider=getattr(spec,"provider",spec)
    api_key=getattr(provider,"api_key",None)
    base_url=getattr(provider,"base_url",None)
    model=getattr(provider,"model",None)
    if not (api_key and base_url and model):
        endpoint=getattr(provider,"endpoint",None)
        credential_env=getattr(provider,"credential_env","")
        model=getattr(provider,"model",None)
        if not endpoint or not model:
            return None
        api_key=os.getenv(str(credential_env),"") if credential_env else ""
        if credential_env and not api_key:
            return {"ok":False,"category":"missing_credentials","http_status":None,"latency_ms":0.0}
        base_url=str(endpoint)
        if not base_url.endswith("/chat/completions"):
            base_url=base_url.rstrip("/")+"/chat/completions"
    else:
        base_url=f"{str(base_url).rstrip('/')}/chat/completions"
    return await probe_openai_compatible(base_url,str(api_key or ""),str(model))
