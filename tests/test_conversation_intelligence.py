from app.core.bitey import _is_greeting
from app.services.problem_state_service import build_problem_state
from app.services.contextual_resolution import resolve_context


def test_greeting_detection_uses_current_core_contract():
    assert _is_greeting("hola") is True
    assert _is_greeting("holla") is False
    assert _is_greeting("Hola Bitey") is False


def test_contextual_followup_preserves_current_problem():
    history = [
        {"sender_type": "customer", "message_content": "Mi celular tiene la pantalla rota", "service_id": None},
    ]

    state = build_problem_state(history, "¿Cuánto cuesta repararlo?")
    resolved = resolve_context(state, "¿Cuánto cuesta repararlo?", history)

    assert resolved["active_category"] == "display"
    assert resolved["active_object"] == "phone"
    assert resolved["active_goal"] in {"SOLVE_PROBLEM", "QUOTE"}
    assert resolved["is_follow_up"] is True


def test_explicit_new_problem_replaces_previous_context():
    history = [
        {"sender_type": "customer", "message_content": "Mi PC está lenta", "service_id": None},
    ]

    state = build_problem_state(history, "La impresora no imprime")
    resolved = resolve_context(state, "La impresora no imprime", history)

    assert resolved["active_category"] == "printing"
    assert resolved["active_problem"] == "problema de impresión"
    assert resolved["is_follow_up"] is False
