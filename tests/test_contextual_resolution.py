from app.services.contextual_resolution import resolve_context


def test_request_details_do_not_become_diagnostic_problem():
    history = [
        {"sender_type": "customer", "message_content": "Hola, quisiera instalar cámaras"},
        {"sender_type": "bitey", "ai_response": "¿Cuántas cámaras necesitas?"},
    ]
    raw = {
        "active_problem": "problema de cámara/vídeo",
        "active_category": "camera",
        "active_object": "camera",
        "entity_only": True,
        "confirmed_facts": [
            {"type": "object", "value": "camera"},
            {"type": "problem", "value": "problema de cámara/vídeo"},
        ],
        "confidence": 0.72,
    }
    state = resolve_context(raw, "Es una vivienda, 2 cámaras, una afuera y otra adentro", history)
    assert state["active_problem"] is None
    assert state["active_category"] is None
    assert state["active_goal"] == "REQUEST_SERVICE"
    assert state["state"] == "ENTITY_UPDATE"
    assert not state["hypotheses"]
    assert all(f["type"] != "problem" for f in state["confirmed_facts"])


def test_explicit_symptom_does_not_get_suppressed():
    history = [
        {"sender_type": "customer", "message_content": "Hola, quisiera instalar cámaras"},
    ]
    raw = {
        "active_problem": "problema de cámara/vídeo",
        "active_category": "camera",
        "active_object": "camera",
        "entity_only": False,
        "confirmed_facts": [{"type": "problem", "value": "problema de cámara/vídeo"}],
    }
    state = resolve_context(raw, "la cámara no muestra imagen", history)
    assert state["active_problem"] == "problema de cámara/vídeo"
    assert state["active_category"] == "camera"
