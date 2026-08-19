import pytest

from app.services.ai_council import AICouncil, AIAnswer, CostGate


def test_cost_gate_disabled_by_default():
    assert CostGate().allow(confidence=0.1, complexity="ambiguous") is False


def test_cost_gate_allows_complex_when_enabled(monkeypatch):
    monkeypatch.setenv("AI_COUNCIL_ENABLED", "true")
    assert CostGate().allow(confidence=0.2, complexity="ambiguous") is True


def test_cost_gate_avoids_simple_question(monkeypatch):
    monkeypatch.setenv("AI_COUNCIL_ENABLED", "true")
    assert CostGate().allow(confidence=0.99, complexity="simple") is False


class GoodProvider:
    name = "test-good"

    async def answer(self, question, context):
        return AIAnswer(provider=self.name, text="Use the model-specific repair workflow.", confidence=0.9)


class BadProvider:
    name = "test-bad"

    async def answer(self, question, context):
        raise RuntimeError("provider unavailable")


@pytest.mark.asyncio
async def test_provider_failure_does_not_break_council(monkeypatch):
    monkeypatch.setenv("AI_COUNCIL_ENABLED", "true")
    result = await AICouncil([GoodProvider(), BadProvider()]).consult(
        "How do I replace a phone screen?", {}, local_confidence=0.2, complexity="technical_complex"
    )
    assert result["consulted"] is True
    assert len(result["answers"]) == 1
    assert result["answers"][0]["provider"] == "test-good"
