"""Tests for conservative external-AI evaluation."""
from app.ai.evaluator import evaluate_candidates


def test_empty_candidates_are_not_learning():
    result = evaluate_candidates([])
    assert result["learning_candidate"] is False
    assert result["consensus"] is None


def test_matching_candidates_create_consensus():
    candidates = [
        {"provider": "provider-a", "answer": "screen_repair"},
        {"provider": "provider-b", "answer": "screen_repair"},
    ]
    result = evaluate_candidates(candidates, core_confidence=0.8)
    assert result["consensus"] == "screen_repair"
    assert result["learning_candidate"] is True
