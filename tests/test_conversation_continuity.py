from app.services.problem_state_service import build_problem_state
from app.services.contextual_resolution import resolve_context


def test_mobile_screen_followup_preserves_problem_context():
    history = [
        {"sender_type": "customer", "message_content": "Necesito reparar mi teléfono", "service_id": None},
        {"sender_type": "ai", "message_content": "¿Qué problema presenta?", "service_id": None},
        {"sender_type": "customer", "message_content": "Pantalla rota", "service_id": None},
    ]

    state = build_problem_state(history, "Es un teléfono móvil")
    resolved = resolve_context(state, "Es un teléfono móvil", history)

    assert resolved["active_object"] == "phone"
    assert resolved["active_problem"] is not None
    assert resolved["active_category"] == "display"
    assert resolved["is_follow_up"] is True


def test_new_problem_does_not_inherit_unrelated_previous_category():
    history = [
        {"sender_type": "customer", "message_content": "Mi PC está lenta", "service_id": None},
        {"sender_type": "ai", "message_content": "Vamos a revisar el rendimiento.", "service_id": None},
    ]

    state = build_problem_state(history, "La impresora no imprime")
    resolved = resolve_context(state, "La impresora no imprime", history)

    assert resolved["active_category"] == "printing"
    assert resolved["active_category"] != "performance"
    assert resolved["is_follow_up"] is False
