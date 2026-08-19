from app.ai.web_intelligence import _normalise_result, _verify, build_queries, needs_web, _domain_score


def test_current_question_requires_web():
    assert needs_web("What is the latest Windows version?", intent="software_update", knowledge_found=True)


def test_known_simple_question_does_not_require_web():
    assert not needs_web("How do I open a ticket?", intent="support", knowledge_found=True)


def test_query_rewriting_is_bounded():
    queries = build_queries("What is the latest Windows version?", intent="software_update")
    assert 1 <= len(queries) <= 3
    assert all(queries)


def test_official_domains_rank_higher():
    assert _domain_score("https://support.microsoft.com/example") > _domain_score("https://example-blog.test/article")


def test_source_scoring_prefers_authoritative_domain():
    result = _normalise_result(
        {"url": "https://learn.microsoft.com/test", "title": "Windows documentation", "snippet": "Windows update guidance"},
        "Windows update guidance",
    )
    assert result is not None
    assert result["authority_score"] >= 0.98
    assert result["score"] > 0.7


def test_verification_requires_independent_corroboration():
    results = [
        {"domain": "learn.microsoft.com", "score": 0.95, "title": "Windows update", "snippet": "Windows update requires restart and version support"},
        {"domain": "support.example.org", "score": 0.90, "title": "Windows update", "snippet": "Windows update requires restart and version support"},
    ]
    verification = _verify(results, "Windows update")
    assert verification["verified"] is True
    assert verification["independent_domains"] == 2
