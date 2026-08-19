from app.ai.web_intelligence import build_queries, needs_web, _domain_score


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
