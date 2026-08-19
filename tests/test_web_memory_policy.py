from app.ai.web_intelligence import build_queries, needs_web, _normalise_result


def test_build_queries_stays_bounded():
    queries = build_queries("what is the latest Windows version?", intent="software_update", max_queries=3)
    assert 1 <= len(queries) <= 3
    assert any("official documentation" in query for query in queries)


def test_current_questions_require_live_web():
    assert needs_web("What is the latest Windows version?", intent="software_update", knowledge_found=True)


def test_missing_knowledge_can_trigger_web():
    assert needs_web("I need a detailed troubleshooting procedure for this unusual error", knowledge_found=False)


def test_normalised_result_keeps_source_metadata():
    item = _normalise_result(
        {"url": "https://learn.microsoft.com/test", "title": "Windows documentation", "content": "Official Windows guidance"},
        "Windows documentation",
    )
    assert item is not None
    assert item["domain"] == "learn.microsoft.com"
    assert item["authority_score"] > 0.9
