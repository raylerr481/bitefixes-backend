import asyncio

from app.ai.registry import AIProviderRegistry, ProviderSpec
from app.ai.runtime import build_ai_orchestrator


class DummyProvider:
    async def generate(self, prompt, *, context=None):
        return f"ok:{prompt}"


def test_registry_orders_enabled_providers_by_priority():
    registry = AIProviderRegistry()
    registry.register(ProviderSpec("slow", True, 20, "free", ("general_reasoning",), DummyProvider()))
    registry.register(ProviderSpec("fast", True, 5, "free", ("general_reasoning",), DummyProvider()))
    assert [p.name for p in registry.available("general_reasoning")] == ["fast", "slow"]


def test_runtime_is_safe_without_provider_keys(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    orchestrator = build_ai_orchestrator()
    assert orchestrator.choose("general_reasoning") is None


def test_orchestrator_uses_selected_provider():
    registry = AIProviderRegistry()
    registry.register(ProviderSpec("dummy", True, 1, "free", ("general_reasoning",), DummyProvider()))
    orchestrator = __import__("app.ai.orchestrator", fromlist=["AIOrchestrator"]).AIOrchestrator(registry)
    result = asyncio.run(orchestrator.ask("hello"))
    assert result["status"] == "ok"
    assert result["provider"] == "dummy"
    assert result["answer"] == "ok:hello"
