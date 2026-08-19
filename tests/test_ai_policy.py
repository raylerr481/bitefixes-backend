"""Tests for governed external-AI consultation decisions."""
from app.ai.consultation_gate import evaluate


def test_high_confidence_stays_inside_bitey():
    decision = evaluate(confidence=0.98, complexity=0.1, novelty=0.0, knowledge_gap=0.0, business_impact=0.1)
    assert decision.consult is False
    assert decision.reason == "core_sufficient"


def test_complex_low_confidence_can_consult():
    decision = evaluate(confidence=0.55, complexity=0.9, novelty=0.8, knowledge_gap=0.8, business_impact=0.8)
    assert decision.consult is True


def test_cost_guard_blocks_expensive_consultation():
    decision = evaluate(confidence=0.2, complexity=1, novelty=1, knowledge_gap=1, business_impact=1, estimated_cost=1)
    assert decision.consult is False
    assert decision.reason == "cost_guard"
