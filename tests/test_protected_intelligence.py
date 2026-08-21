from app.ai.privacy_engine import build_external_context, sanitize
from app.ai.evaluator import evaluate_candidates
from app.ai.learning_engine import learn_pattern
from app.ai.trust_engine import rank_candidates


def test_external_context_removes_identity_and_secrets():
    context = build_external_context(
        intent={"intent": "mobile_repair", "confidence": 0.9},
        business_context={"company_id": 7, "customer": {"full_name": "Juan Perez", "email": "juan@example.com", "phone": "+55 51999999999"}, "api_key": "secret"},
        knowledge={"symptom": "telefono roto"},
    )
    text = str(context)
    assert "Juan Perez" not in text
    assert "juan@example.com" not in text
    assert "+55 51999999999" not in text
    assert "secret" not in text
    assert "mobile_repair" in text


def test_ai_consensus_can_become_learning_candidate():
    result = evaluate_candidates([
        {"provider": "groq", "answer": "mobile_repair"},
        {"provider": "huggingface", "answer": "mobile_repair"},
    ], core_confidence=0.9)
    assert result["consensus"] == "mobile_repair"
    assert result["learning_candidate"] is True


def test_learning_requires_validation(monkeypatch):
    monkeypatch.setattr("app.ai.learning_engine.database.table", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("db")))
    result = learn_pattern(message="telefono roto", intent="mobile_repair", evaluation={"confidence": 0.9, "consensus": "mobile_repair"})
    assert result["stored"] is False
    assert result["candidate"]["pattern_hash"]


def test_trust_ranking_uses_neutral_prior(monkeypatch):
    monkeypatch.setattr("app.ai.trust_engine.database.table", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("db")))
    ranked = rank_candidates([
        {"provider": "groq", "answer": "a"},
        {"provider": "hf", "answer": "b"},
    ])
    assert [item["trust_score"] for item in ranked] == [0.5, 0.5]


def test_sanitize_redacts_free_text():
    value = sanitize("contacto juan@example.com y 51999999999")
    assert "@example.com" not in value
    assert "51999999999" not in value
