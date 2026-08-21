from app.ai.knowledge_promotion import KnowledgePromotion


def test_ai_repetition_is_not_independent_evidence():
    decision = KnowledgePromotion().evaluate([0.30, 0.30, 0.25], 1, 2)
    assert decision.status == "candidate"


def test_conflict_blocks_promotion():
    decision = KnowledgePromotion().evaluate([1.0, 0.9], 2, 3, conflicts=1)
    assert decision.status == "blocked"


def test_independent_sources_plus_verification_promote():
    decision = KnowledgePromotion().evaluate([1.0, 0.9], 2, 2)
    assert decision.status == "trusted"
    assert decision.score >= 0.75
