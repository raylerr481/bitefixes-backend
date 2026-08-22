from app.services.bitey_gateway import _derive_conversation_state


def test_mobile_screen_followup_inherits_device_and_problem():
    history = [
        {"sender_type": "customer", "message_content": "Necesito reparar mi teléfono", "service_id": None},
        {"sender_type": "ai", "message_content": "Claro. ¿Qué problema presenta?", "service_id": None},
        {"sender_type": "customer", "message_content": "Pantalla rota", "service_id": None},
    ]

    state = _derive_conversation_state(history, "Es un teléfono móvil")

    assert state["active_object"] == "teléfono móvil"
    assert state["active_problem"] == "pantalla rota/quebrada"
    assert state["active_topic"] == "reparación de teléfono móvil"
    assert state["stage"] == "diagnosis"
    assert state["is_follow_up"] is True


def test_broken_mobile_followup_does_not_reset_context():
    history = [
        {"sender_type": "customer", "message_content": "Necesito reparar mi teléfono", "service_id": None},
        {"sender_type": "customer", "message_content": "Pantalla rota", "service_id": None},
    ]

    state = _derive_conversation_state(history, "El móvil está quebrado")

    assert state["active_object"] == "teléfono móvil"
    assert state["active_problem"] == "pantalla rota/quebrada"
    assert state["active_topic"] == "reparación de teléfono móvil"
