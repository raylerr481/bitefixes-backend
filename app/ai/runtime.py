"""Runtime wiring for Bitey's governed cognitive council."""
from __future__ import annotations

import os
from typing import Any

from .cloudflare_provider import CloudflareAIProvider
from .groq_provider import GroqProvider
from .openrouter_provider import OpenRouterProvider, QWEN_FREE_MODEL, DEEPSEEK_FREE_MODEL
from .openai_compatible_provider import OpenAICompatibleProvider
from .orchestrator import AIOrchestrator
from .registry import AIProviderRegistry, ProviderSpec

# Hugging Face Inference Providers currently documents Qwen3-32B on Groq and
# supports the OpenAI-compatible router at /v1. Keep the default configurable.
DEFAULT_HF_MODEL = "Qwen/Qwen3-32B:groq"


def _register_database_models(registry: AIProviderRegistry, company_id: int | None) -> None:
    """Load enabled open-model metadata from Supabase incrementally."""
    try:
        from app.supabase_client import supabase
        query = supabase.table("bitey_ai_models").select(
            "provider,model_name,transport,endpoint_url,credential_env,capabilities,cost_class,priority,enabled"
        ).eq("enabled", True).order("priority")
        if company_id is not None:
            query = query.or_(f"company_id.is.null,company_id.eq.{int(company_id)}")
        else:
            query = query.is_("company_id", "null")
        rows = (query.execute().data or [])
        for row in rows:
            if row.get("transport") != "openai_compatible" or not row.get("endpoint_url"):
                continue
            name = f"{row.get('provider', 'open')}-{row.get('model_name')}"
            provider = OpenAICompatibleProvider(
                name=name,
                model=str(row.get("model_name")),
                endpoint=str(row.get("endpoint_url")),
                credential_env=str(row.get("credential_env") or ""),
                enabled=bool(row.get("enabled", True)),
            )
            registry.register(ProviderSpec(
                name=name,
                enabled=provider.enabled,
                priority=int(row.get("priority", 100)),
                cost_class=str(row.get("cost_class") or "free"),
                capabilities=tuple(row.get("capabilities") or ("general_reasoning",)),
                provider=provider,
            ))
    except Exception as exc:
        print("[AI MODEL REGISTRY WARNING]", type(exc).__name__)


def _register_huggingface(registry: AIProviderRegistry) -> None:
    """Add Hugging Face as an incremental OpenAI-compatible candidate."""
    token = os.getenv("HF_TOKEN", "").strip()
    model = os.getenv("HF_MODEL", DEFAULT_HF_MODEL).strip()
    if not token or not model:
        print("[AI PROVIDER] huggingface=not_configured")
        return
    endpoint = os.getenv("HF_ENDPOINT", "https://router.huggingface.co/v1").strip()
    provider = OpenAICompatibleProvider(
        name="huggingface",
        model=model,
        endpoint=endpoint,
        credential_env="HF_TOKEN",
        enabled=os.getenv("HF_ENABLED", "true").lower() != "false",
    )
    registry.register(ProviderSpec(
        name="huggingface",
        enabled=provider.enabled,
        priority=int(os.getenv("HF_PRIORITY", "30")),
        cost_class="free",
        capabilities=("general_reasoning", "semantic_analysis", "language", "extraction"),
        provider=provider,
    ))
    print(f"[AI PROVIDER] huggingface=registered model={model}")


def build_ai_orchestrator(company_id: int | None = None) -> AIOrchestrator:
    registry = AIProviderRegistry()
    groq = GroqProvider()
    registry.register(ProviderSpec(name="groq", enabled=groq.enabled and os.getenv("GROQ_ENABLED", "true").lower() != "false", priority=int(os.getenv("GROQ_PRIORITY", "5")), cost_class="free", capabilities=("general_reasoning", "semantic_analysis", "language", "extraction"), provider=groq))
    qwen = OpenRouterProvider(model=os.getenv("OPENROUTER_QWEN_MODEL", QWEN_FREE_MODEL))
    registry.register(ProviderSpec(name="qwen-free", enabled=qwen.enabled, priority=int(os.getenv("QWEN_PRIORITY", "10")), cost_class="free", capabilities=("general_reasoning", "semantic_analysis", "language", "extraction"), provider=qwen))
    deepseek = OpenRouterProvider(model=os.getenv("OPENROUTER_DEEPSEEK_MODEL", DEEPSEEK_FREE_MODEL))
    registry.register(ProviderSpec(name="deepseek-free", enabled=deepseek.enabled and os.getenv("DEEPSEEK_ENABLED", "true").lower() != "false", priority=int(os.getenv("DEEPSEEK_PRIORITY", "15")), cost_class="free", capabilities=("general_reasoning", "semantic_analysis", "language", "extraction"), provider=deepseek))
    cloudflare = CloudflareAIProvider()
    registry.register(ProviderSpec(name="cloudflare-free", enabled=cloudflare.enabled, priority=int(os.getenv("CLOUDFLARE_PRIORITY", "20")), cost_class="free", capabilities=("general_reasoning", "semantic_analysis", "language", "extraction"), provider=cloudflare))
    _register_database_models(registry, company_id)
    _register_huggingface(registry)
    return AIOrchestrator(registry)
