from app.services.cognitive_evidence import classify_signals, resolve_evidence


def test_redmi_does_not_trigger_connectivity():
    assert "connectivity" not in classify_signals("Redmi 9A")


def test_model_answer_uses_pending_question():
    decision = resolve_evidence("9a", "¿Cuál es el modelo exacto de tu Redmi?")
    assert decision.relation == "ANSWER_TO_PENDING"
    assert decision.evidence_type == "model"
    assert decision.field == "model"
    assert decision.value == "9a"


def test_model_answer_is_generic():
    decision = resolve_evidence("Latitude 5420", "¿Cuál es el modelo del notebook?")
    assert decision.relation == "ANSWER_TO_PENDING"
    assert decision.field == "model"


def test_explicit_new_symptom_overrides_pending_model():
    decision = resolve_evidence("ahora no carga", "¿Cuál es el modelo?")
    assert decision.relation == "NEW_EVIDENCE"
    assert decision.evidence_type == "symptom"


def test_isolated_short_value_does_not_invent_context():
    decision = resolve_evidence("9a")
    assert decision.relation == "AMBIGUOUS"
    assert decision.evidence_type == "unknown"
