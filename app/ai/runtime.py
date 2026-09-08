"""Runtime wiring for Bitey's governed cognitive council."""
from __future__ import annotations
import os
from typing import Any
import httpx
from .groq_provider import GroqProvider
from .openrouter_provider import OpenRouterProvider, OPENROUTER_FREE_MODEL
from .orchestrator import AIOrchestrator
from .registry import AIProviderRegistry, ProviderSpec


def _register_database_models(registry: AIProviderRegistry, company_id: int | None) -> None:
    try:
        from app.supabase_client import supabase
        query = supabase.table("bitey_ai_models").select("provider,model_name,transport,endpoint_url,credential_env,capabilities,cost_class,priority,enabled").eq("enabled", True).order("priority")
        if company_id is not None: query = query.or_(f"company_id.is.null,company_id.eq.{int(company_id)}")
        else: query = query.is_("company_id", "null")
        for row in (query.execute().data or []):
            if row.get("transport") != "openai_compatible" or not row.get("endpoint_url"): continue
            name = f"{row.get('provider', 'open')}-{row.get('model_name')}"
            model = str(row.get("model_name"))
            if "qwen" in model.lower() or "gemini" in model.lower() or "deepseek" in model.lower():
                print(f"[AI PROVIDER] database_model=blocked model={model}")
                continue
            provider = OpenRouterProvider(model=model) if str(row.get("provider", "")).lower() == "openrouter" else None
            if provider is None:
                continue
            registry.register(ProviderSpec(name=name, enabled=provider.enabled, priority=int(row.get("priority", 100)), cost_class="free", capabilities=tuple(row.get("capabilities") or ("general_reasoning",)), provider=provider))
    except Exception as exc:
        print("[AI MODEL REGISTRY WARNING]", type(exc).__name__)


def build_ai_orchestrator(company_id: int | None = None) -> AIOrchestrator:
    registry = AIProviderRegistry()

    # Primary: keep Groq as requested.
    groq = GroqProvider()
    registry.register(ProviderSpec(
        name="groq",
        enabled=groq.enabled and os.getenv("GROQ_ENABLED", "true").lower() != "false",
        priority=int(os.getenv("GROQ_PRIORITY", "5")),
        cost_class="free",
        capabilities=("general_reasoning", "semantic_analysis", "language", "extraction"),
        provider=groq,
    ))

    # Fallback: OpenRouter's dedicated Free Models Router. It can only select
    # models that are free; paid routing is rejected by OpenRouterProvider.
    openrouter = OpenRouterProvider(model=os.getenv("OPENROUTER_MODEL", OPENROUTER_FREE_MODEL))
    registry.register(ProviderSpec(
        name="openrouter-free",
        enabled=openrouter.enabled,
        priority=int(os.getenv("OPENROUTER_PRIORITY", "10")),
        cost_class="free",
        capabilities=("general_reasoning", "semantic_analysis", "language", "extraction"),
        provider=openrouter,
    ))

    # Only explicitly configured OpenRouter database models may participate,
    # and paid/Qwen/Gemini/DeepSeek models are blocked.
    _register_database_models(registry, company_id)
    return AIOrchestrator(registry)
