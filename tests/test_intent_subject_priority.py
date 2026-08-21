from app.services import intent_service


def _stub_db(monkeypatch):
    monkeypatch.setattr(intent_service, "get_synonyms", lambda: [])
    monkeypatch.setattr(intent_service, "get_company_services", lambda company_id: [])
    monkeypatch.setattr(intent_service, "recover_active_ticket", lambda context: {"intent": "mobile_repair"})
    monkeypatch.setattr(intent_service, "understand_concept", lambda message, context=None: {"concept": {}})
    monkeypatch.setattr(intent_service, "propose_learning", lambda *args, **kwargs: {"status": "candidate"})
    monkeypatch.setattr(intent_service, "record_learning", lambda *args, **kwargs: None)
    monkeypatch.setattr(intent_service, "llm_understand", None)


def test_pc_rota_overrides_mobile_context(monkeypatch):
    _stub_db(monkeypatch)
    result = intent_service.detect_intent("tengo pc rota", 1, {"last_intent": "mobile_repair", "company_id": 1})
    assert result["intent"] == "computer_repair"
    assert result["explicit_intent"] is True
    assert result["confidence"] >= 0.92


def test_repair_windows_overrides_mobile_context(monkeypatch):
    _stub_db(monkeypatch)
    result = intent_service.detect_intent("necesito reparar windows", 1, {"last_intent": "mobile_repair", "company_id": 1})
    assert result["intent"] == "windows_installation"
    assert result["explicit_intent"] is True
    assert result["confidence"] >= 0.92
