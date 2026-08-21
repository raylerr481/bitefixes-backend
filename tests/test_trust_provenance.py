from app.ai.trust_engine import TrustEngine


def test_ai_alone_never_promotes():
    result = TrustEngine().evaluate(
        {"claim": "x"},
        verified=True,
        corroborations=3,
        sources=[
            {"type": "ai", "locator": "model-a"},
            {"type": "ai", "locator": "model-b"},
        ],
    )
    assert result["status"] == "candidate"
    assert not result["promotable"]


def test_independent_verified_sources_can_promote():
    result = TrustEngine().evaluate(
        {"claim": "x"},
        verified=True,
        corroborations=2,
        sources=[
            {"type": "official_documentation", "locator": "official"},
            {"type": "technical_documentation", "locator": "technical"},
        ],
    )
    assert result["status"] == "trusted"
    assert result["promotable"]


def test_conflict_blocks_promotion():
    result = TrustEngine().evaluate(
        {"claim": "x"},
        verified=True,
        corroborations=2,
        conflicts=1,
        sources=[
            {"type": "official_documentation"},
            {"type": "technical_documentation"},
        ],
    )
    assert not result["promotable"]
