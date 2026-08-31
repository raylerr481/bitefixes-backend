from app.services import repair_research_service as research


def test_research_uses_full_cognitive_context(monkeypatch):
    queries = []

    def fake_search(query, limit=8):
        queries.append(query)
        return [{"title": "Redmi 9A screen replacement tutorial", "url": "https://youtube.com/watch?v=screen"}]

    monkeypatch.setattr(research, "_web_search", fake_search)
    result = research.build_repair_research(
        message="quiero un video",
        active_problem="pantalla rota",
        active_category="display",
        active_object="celular",
        active_model="Redmi 9A",
        company_name="BiteFixes",
        industry="technical_support",
    )
    assert result["research_mode"] == "broad_web_and_youtube"
    assert any("Redmi 9A" in q and "pantalla rota" in q for q in queries)
    assert result["youtube"]["results"][0]["url"] == "https://youtube.com/watch?v=screen"
    assert len(result["query_variants"]) >= 3


def test_research_is_not_youtube_only(monkeypatch):
    def fake_search(query, limit=8):
        if query.startswith("site:youtube.com"):
            return [{"title": "YouTube guide", "url": "https://youtube.com/watch?v=1"}]
        return [{"title": "Official service guide", "url": "https://example.com/service-guide"}]

    monkeypatch.setattr(research, "_web_search", fake_search)
    result = research.build_repair_research(
        message="tutorial",
        active_problem="replace keyboard",
        active_object="notebook",
        active_model="Latitude 5420",
        industry="technical_support",
    )
    assert result["web"]
    assert result["youtube"]["results"]
    assert result["research_mode"] == "broad_web_and_youtube"


def test_same_engine_adapts_research_to_different_company_contexts(monkeypatch):
    queries = []

    def fake_search(query, limit=8):
        queries.append(query)
        return []

    monkeypatch.setattr(research, "_web_search", fake_search)
    research.build_repair_research(
        message="quiero un tutorial",
        active_problem="pantalla rota",
        active_model="Redmi 9A",
        industry="technical_support",
        company_name="BiteFixes",
    )
    first_count = len(queries)
    research.build_repair_research(
        message="quiero un tutorial",
        active_problem="mantenimiento",
        active_object="torno industrial",
        industry="industrial_maintenance",
        company_name="FactoryCo",
    )
    second_queries = queries[first_count:]
    assert any("Redmi 9A" in q for q in queries[:first_count])
    assert any("torno industrial" in q and "industrial_maintenance" in q for q in second_queries)


def test_tutorial_request_detection_is_generic():
    assert research.tutorial_requested("¿puedes pasarme un video para hacerlo yo?")
    assert research.tutorial_requested("necesito una guía paso a paso")
    assert research.tutorial_requested("can you show me a walkthrough?")
