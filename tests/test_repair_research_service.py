from app.services.repair_research_service import build_repair_research, tutorial_requested


def test_tutorial_request_is_detected_without_device_specific_rules():
    assert tutorial_requested("¿Puedes pasarme un video de YouTube de cómo hacerlo?")
    assert tutorial_requested("quiero una guía paso a paso para repararlo yo")
    assert not tutorial_requested("¿ustedes reparan la pantalla?")


def test_research_query_is_built_from_active_context():
    result = build_repair_research(
        message="¿cómo hacerlo?",
        active_problem="broken screen",
        active_category="display",
        active_object="phone",
        active_model="Redmi 9A",
    )
    assert result["requested"] is True
    assert "Redmi 9A" in result["query"]
    assert result["youtube"]["search_url"].startswith("https://www.youtube.com/results?search_query=")
    assert result["safety"]


def test_unknown_model_does_not_block_generic_research():
    result = build_repair_research(
        message="quiero un tutorial para reparar la pantalla",
        active_problem="broken screen",
        active_category="display",
        active_object="phone",
        active_model=None,
    )
    assert result["requested"] is True
    assert "broken screen" in result["query"]
