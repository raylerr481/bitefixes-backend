from app.cognitive.cognitive_state import CognitiveState


def test_state_contains_portable_context_dimensions():
    state = CognitiveState(
        company_id=10,
        channel="whatsapp",
        conversation_id="c-1",
        user_id="u-1",
        active_problem="customer_assistant",
        active_goal="increase_sales",
        active_service="ai_assistant",
        known_facts={"channel": "whatsapp"},
        new_facts={"business_goal": "sales"},
        missing_facts=["catalog"],
        questions_asked=["business_type"],
        evidence=[{"key": "channel", "source": "user", "verified": True}],
        contradictions=[],
        hypotheses=[{"content": "CRM may exist", "source": "llm"}],
        next_best_action="ask_catalog",
    )
    data = state.to_dict()
    assert data["company_id"] == 10
    assert data["channel"] == "whatsapp"
    assert data["active_goal"] == "increase_sales"
    assert data["known_facts"]["channel"] == "whatsapp"
    assert data["hypotheses"][0]["source"] == "llm"
