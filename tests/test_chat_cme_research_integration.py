"""Integration contract: /chat -> gateway -> decision engine -> consultation -> CME research."""
from app.ai import consultation_service


def test_consultation_passes_company_id_into_cme_research(monkeypatch):
    calls = []

    def fake_search_web(message, *, intent=None, company_id=None, limit=None):
        calls.append({"message": message, "intent": intent, "company_id": company_id})
        return {
            "used": True,
            "company_id": company_id,
            "cme": "cme-research-v1",
            "results": [{
                "title": f"Evidence {company_id}",
                "url": f"https://example.com/{company_id}",
                "snippet": f"tenant={company_id}",
                "rank_score": 0.9,
                "company_id": company_id,
            }],
            "grounding_status": "grounded",
            "learning_candidate": False,
        }

    monkeypatch.setattr(consultation_service, "search_web", fake_search_web)
    monkeypatch.setattr(consultation_service, "needs_web", lambda *args, **kwargs: True)
    monkeypatch.setattr(consultation_service, "record_web_candidate", lambda **kwargs: None)
    monkeypatch.setattr(
        consultation_service,
        "consult",
        lambda message, language, context, max_providers: [{
            "provider": "test",
            "answer": "Respuesta basada en la evidencia disponible.",
        }],
    )
    monkeypatch.setattr(consultation_service, "record_candidate", lambda **kwargs: None)

    base = {
        "company_id": 111,
        "business_context": {"company_id": 111},
        "memory": {"conversation_id": 1, "history": []},
        "conversation_problem": {},
        "knowledge_gap": 1.0,
    }
    a = consultation_service.consult_if_valuable(
        company_id=111, message="investigate current network issue", language="en",
        intent={}, context=base, conversation_id=1,
    )
    b = consultation_service.consult_if_valuable(
        company_id=222, message="investigate current network issue", language="en",
        intent={}, context={**base, "company_id": 222}, conversation_id=2,
    )

    assert [x["company_id"] for x in calls] == [111, 222]
    assert a["web_grounding"]["company_id"] == 111
    assert b["web_grounding"]["company_id"] == 222
    assert a["web_grounding"]["results"][0]["company_id"] != b["web_grounding"]["results"][0]["company_id"]
    assert a["web_grounding"]["cme"] == b["web_grounding"]["cme"] == "cme-research-v1"
