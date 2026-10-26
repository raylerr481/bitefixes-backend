from app.ai.consultation_service import _coherence_score, _explicit_place_conflict, _select_coherent


def test_rejects_answer_about_wrong_country_for_explicit_weather_question():
    question = "¿Qué tiempo hace en España?"
    answer = "En Mimaropa, Filipinas, la temperatura registrada es 26.7 °C."
    score, reasons = _coherence_score(answer, question, {})
    assert score < 0.60
    assert any(reason.startswith("answer_mentions_unrequested_place:") for reason in reasons)


def test_accepts_answer_about_requested_country():
    question = "¿Qué tiempo hace en España?"
    answer = "En España hay cielos parcialmente nublados y temperaturas suaves."
    score, reasons = _coherence_score(answer, question, {})
    assert score >= 0.60
    assert not any(reason.startswith("answer_mentions_unrequested_place:") for reason in reasons)


def test_does_not_flag_explicit_place_comparison():
    question = "Compara el clima de España y Filipinas"
    answer = "España tiene estaciones más marcadas; Filipinas tiene clima tropical."
    assert _explicit_place_conflict(answer, question) is None


def test_candidate_selector_rejects_wrong_place_candidate():
    results = [
        {"provider": "provider-a", "answer": "En Mimaropa, Filipinas, hay 26.7 °C."},
        {"provider": "provider-b", "answer": "En España, el tiempo varía según la región."},
    ]
    selected, evaluated = _select_coherent(results, "¿Qué tiempo hace en España?", {})
    assert selected is not None
    assert selected["provider"] == "provider-b"
    assert len(evaluated) == 2


def test_general_answer_gate_does_not_require_keyword_overlap():
    question = "¿Por qué el cielo se ve azul?"
    answer = "La atmósfera dispersa con mayor intensidad las longitudes de onda cortas de la luz solar."
    score, reasons = _coherence_score(answer, question, {})
    assert score >= 0.60
    assert reasons == []


def test_rejects_foreign_weather_observation_even_if_requested_country_is_named():
    question = "¿Qué tiempo hace en España?"
    answer = "En España, Mimaropa, Filipinas, la temperatura es 26.7 °C."
    score, reasons = _coherence_score(answer, question, {})
    assert score < 0.60
    assert any(reason.startswith("answer_mentions_unrequested_place:") for reason in reasons)
