from app.cognitive.context_state import CognitiveState
from app.cognitive.reasoning_loop import CognitiveReasoningLoop


def test_merge_preserves_established_context():
    state = CognitiveState(intent="cctv_installation", service_id=5, goal="solve request")
    state.merge({"known": {"camera_count": 2}, "entity": {"property_type": "residential"}})
    assert state.intent == "cctv_installation"
    assert state.service_id == 5
    assert state.known["camera_count"] == 2
    assert state.entity["property_type"] == "residential"


def test_followup_keeps_active_intent_from_memory():
    loop = CognitiveReasoningLoop()
    state = loop.build_state(
        customer_id=1,
        company_id=1,
        conversation_id="demo-continuity-001",
        language="es",
        message="vivienda, 2 camaras, una afuera y otra adentro",
        memory={
            "last_intent": "cctv_installation",
            "last_service": 5,
            "goal": "instalar cámaras",
            "known": {"camera_count": 2},
        },
        intent={},
        problem={"classification": "CONTINUATION"},
    )
    assert state.intent == "cctv_installation"
    assert state.service_id == 5
    assert state.problem_state == "CONTINUATION"
    assert loop.decide_next_action(state) == "advance_service"


def test_missing_context_requests_clarification():
    loop = CognitiveReasoningLoop()
    state = CognitiveState(intent="computer_repair", missing=["symptom"])
    assert loop.decide_next_action(state) == "ask_clarification"


def test_contradiction_has_priority():
    loop = CognitiveReasoningLoop()
    state = CognitiveState(intent="computer_repair", contradictions=[{"field": "device"}])
    assert loop.decide_next_action(state) == "resolve_contradiction"
