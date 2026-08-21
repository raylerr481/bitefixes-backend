from app.services import intent_service
from app.services.workflows import mobile_repair


def test_greeting_never_becomes_service_intent(monkeypatch):
    monkeypatch.setattr(intent_service, "get_synonyms", lambda: [{"keyword": "hola", "intent": "mobile_repair", "weight": 10}])
    monkeypatch.setattr(intent_service, "get_company_services", lambda company_id: [
        {"intent": "mobile_repair", "name": "Hola", "description": "Hola", "is_active": True}
    ])

    result = intent_service.detect_intent("hola", company_id=1)

    assert result["intent"] is None
    assert result["confidence"] == 0.0


def test_intent_confidence_is_normalized(monkeypatch):
    monkeypatch.setattr(intent_service, "get_synonyms", lambda: [])
    monkeypatch.setattr(intent_service, "get_company_services", lambda company_id: [])

    result = intent_service.detect_intent("telefono roto", company_id=1)

    assert result["intent"] == "mobile_repair"
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["confidence"] == 0.99


def test_mobile_repair_starts_with_diagnosis_without_ticket():
    result = mobile_repair.execute("tengo telefono roto", language="es")

    assert result["success"] is False
    assert result["diagnostic_pending"] is True
    assert "diagnóstico" in result["response"]


def test_mobile_diagnosis_request_does_not_create_ticket():
    result = mobile_repair.execute("realiza el diagnostico", language="es")

    assert result["success"] is False
    assert result["diagnostic_pending"] is True
    assert "¿Qué le sucede" in result["response"]


def test_mobile_repair_can_progress_to_ticket_after_explicit_action():
    result = mobile_repair.execute("quiero reparar la pantalla rota y necesito presupuesto", language="es")

    assert result["success"] is True
    assert result["diagnostic_pending"] is False
    assert result["metadata"]["issue_type"] == "screen"
