from app.services.response_builder import build_response


def test_ai_candidate_is_used_for_conversation():
    decision = {
        "action": "conversation",
        "create_ticket": False,
        "requires_quote": False,
        "response": "Respuesta determinista",
        "ai_consultation": {
            "used": True,
            "suggestions": [{"provider": "groq", "answer": "Respuesta razonada por IA"}],
            "evaluation": {"selected": {"provider": "groq", "answer": "Respuesta razonada por IA"}},
        },
    }
    result = build_response(decision=decision, language="es")
    assert result == "Respuesta razonada por IA"
    assert decision["response_source"] == "external_ai"


def test_ai_candidate_cannot_replace_ticket_response():
    decision = {
        "action": "conversation",
        "create_ticket": True,
        "requires_quote": False,
        "response": "Respuesta de flujo",
        "ai_consultation": {
            "used": True,
            "suggestions": [{"provider": "groq", "answer": "No debe sustituir el flujo"}],
            "evaluation": {"selected": {"provider": "groq", "answer": "No debe sustituir el flujo"}},
        },
    }
    result = build_response(decision=decision, language="es")
    assert result == "Respuesta de flujo"
