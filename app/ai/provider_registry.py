"""Safe AI provider discovery, health, capability and routing registry."""
from __future__ import annotations
import os, time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List

@dataclass
class ProviderCandidate:
    provider: str
    model: str
    endpoint: str
    capabilities: List[str]
    enabled: bool = False
    status: str = "unknown"
    priority: int = 100
    last_success: float | None = None
    last_failure: float | None = None
    http_status: int | None = None
    latency_ms: float | None = None
    quality_score: float | None = None
    failure_count: int = 0

DEFAULT_PROVIDERS = [
    ProviderCandidate("groq", "openai/gpt-oss-120b", "https://api.groq.com/openai/v1/chat/completions", ["chat", "reasoning", "tools", "web"], priority=10),
    ProviderCandidate("groq", "groq/compound-mini", "https://api.groq.com/openai/v1/chat/completions", ["chat", "reasoning", "web", "tools"], priority=15),
    ProviderCandidate("cloudflare", "@cf/zai-org/glm-4.7-flash", "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}", ["chat", "reasoning"], priority=20),
    ProviderCandidate("openrouter", "openrouter/free", "https://openrouter.ai/api/v1/chat/completions", ["chat", "reasoning", "dynamic_free"], priority=30),
    ProviderCandidate("huggingface", "dynamic", "https://router.huggingface.co/v1/chat/completions", ["chat", "model_pool"], priority=40),
]

def credentials_configured(provider: str) -> bool:
    names = {"groq": ("GROQ_API_KEY",), "cloudflare": ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"), "openrouter": ("OPENROUTER_API_KEY",), "huggingface": ("HF_TOKEN",)}
    return bool(names.get(provider)) and all(os.getenv(k) for k in names[provider])

def discover_candidates() -> List[Dict[str, Any]]:
    result=[]
    for candidate in DEFAULT_PROVIDERS:
        item=asdict(candidate)
        item["credentials_configured"]=credentials_configured(candidate.provider)
        item["production_eligible"]=False
        result.append(item)
    return result

def record_health(candidate: Dict[str, Any], *, ok: bool, http_status: int | None=None, latency_ms: float | None=None, quality_score: float | None=None) -> Dict[str, Any]:
    now=time.time(); candidate=dict(candidate)
    candidate.update(status="healthy" if ok else "unhealthy", http_status=http_status, latency_ms=latency_ms, quality_score=quality_score, last_success=now if ok else candidate.get("last_success"), last_failure=None if ok else now, failure_count=0 if ok else int(candidate.get("failure_count",0))+1)
    candidate["production_eligible"]=bool(ok and candidate.get("credentials_configured"))
    return candidate

def select_provider(candidates: List[Dict[str, Any]], capabilities: List[str] | None=None) -> Dict[str, Any] | None:
    required=set(capabilities or ["chat","reasoning"]); eligible=[]
    for c in candidates:
        if c.get("production_eligible") and required.issubset(set(c.get("capabilities",[]))): eligible.append(c)
    eligible.sort(key=lambda x:(-float(x.get("quality_score") or 0), x.get("priority",100), float(x.get("latency_ms") or 999999)))
    return eligible[0] if eligible else None
