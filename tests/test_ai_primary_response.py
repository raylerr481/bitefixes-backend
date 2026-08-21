from app.services.response_builder import build_final_response


def test_ai_reply_is_primary_for_diagnosis():
    decision = {
        "action": "conversation",
        "response": "Respuesta determinista antigua.",
        "llm": {
            "used": True,
            "provider": "groq",
            "model": "test-model",
            "reply": "Vamos a diagnosticar Windows. ¿Qué error aparece al iniciar?",
        },
    }
    result = build_final_response(decision=decision, language="es")
    assert result == "Vamos a diagnosticar Windows. ¿Qué error aparece al iniciar?"
    assert decision["response_source"] == "external_ai_primary"
    assert decision["metadata"]["ai_role"] == "primary_cognitive"


def test_business_ticket_response_remains_authoritative():
    decision = {
        "action": "ticket",
        "create_ticket": True,
        "response": "Solicitud registrada.",
        "llm": {"used": True, "provider": "groq", "reply": "No debería sustituir el ticket."},
    }
    ticket = {"ticket_code": "BF-TEST-001"}
    result = build_final_response(decision=decision, ticket=ticket, language="es")
    assert "No debería sustituir el ticket." not in result
    assert "BF-TEST-001" in result
