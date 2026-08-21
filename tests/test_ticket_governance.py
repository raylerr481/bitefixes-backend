import pytest

from app.ai import ticket_governance
from app.ai.ticket_governance import (
    TicketGovernanceError,
    evaluate_ticket_closure,
    evaluate_ticket_creation,
    execute_ticket_creation,
)


def council(creator=True, closer=True):
    return [
        {"provider": "groq", "recommend_create_ticket": creator, "recommend_close_ticket": closer},
        {"provider": "deepseek-free", "recommend_create_ticket": creator, "recommend_close_ticket": closer},
        {"provider": "qwen-free", "recommend_create_ticket": False, "recommend_close_ticket": False},
    ]


def test_ticket_creation_requires_council_consensus_and_context():
    result = evaluate_ticket_creation(
        context={"customer_id": 7, "problem": "wifi drops", "active_ticket": None},
        provider_results=council(),
    )
    assert result["approved"] is True
    assert result["executor"] == "groq"
    assert set(result["approvals"]) == {"groq", "deepseek-free"}


def test_one_ai_cannot_create_a_ticket_alone():
    result = evaluate_ticket_creation(
        context={"customer_id": 7, "problem": "wifi drops", "active_ticket": None},
        provider_results=[{"provider": "groq", "recommend_create_ticket": True}],
    )
    assert result["approved"] is False
    assert result["executor"] is None


def test_existing_active_ticket_blocks_duplicate_creation():
    result = evaluate_ticket_creation(
        context={"customer_id": 7, "problem": "wifi drops", "active_ticket": {"id": 10}},
        provider_results=council(),
    )
    assert result["approved"] is False
    assert "active_ticket_already_exists" in result["missing"]


def test_groq_is_the_only_delegated_ticket_executor(monkeypatch):
    called = {}

    def fake_create_ticket(**data):
        called.update(data)
        return {"id": 99}

    monkeypatch.setattr(ticket_governance, "create_ticket", fake_create_ticket)
    decision = {"approved": True, "executor": "groq"}
    result = execute_ticket_creation(
        decision=decision,
        ticket_data={"customer_id": 7, "title": "Wi-Fi instability"},
    )
    assert result == {"id": 99}
    assert called["customer_id"] == 7


def test_non_delegated_ai_cannot_execute_ticket_write():
    with pytest.raises(TicketGovernanceError, match="invalid_ticket_executor"):
        execute_ticket_creation(
            decision={"approved": True, "executor": "deepseek-free"},
            ticket_data={"customer_id": 7},
        )


def test_ticket_closure_requires_evidence_user_confirmation_and_consensus():
    result = evaluate_ticket_closure(
        context={
            "ticket_id": 99,
            "status": "in_progress",
            "resolution_evidence": "AP channel changed and connection remained stable for 30 minutes",
            "user_confirmed": True,
        },
        provider_results=council(),
    )
    assert result["approved"] is True
    assert result["executor"] == "groq"


def test_ticket_closure_stays_open_without_proof_of_resolution():
    result = evaluate_ticket_closure(
        context={
            "ticket_id": 99,
            "status": "in_progress",
            "resolution_evidence": "",
            "user_confirmed": False,
        },
        provider_results=council(),
    )
    assert result["approved"] is False
    assert result["action"] == "continue_work"
