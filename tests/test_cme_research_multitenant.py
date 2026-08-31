from app.ai.cme_research import BiteyCME
from app.ai.research_result import ResearchResult
from app.ai import web_intelligence


def test_cme_ranks_generic_evidence_without_domain_rules():
    results = [
        ResearchResult(
            title="Low relevance", url="https://example.org/a", company_id=10,
            relevance_score=0.20, authority_score=0.90, verification_score=0.90,
        ),
        ResearchResult(
            title="High relevance", url="https://example.org/b", company_id=10,
            relevance_score=0.95, authority_score=0.70, verification_score=0.70,
        ),
    ]
    ranked = BiteyCME.rank(results, company_id=10)
    assert [item["title"] for item in ranked] == ["High relevance", "Low relevance"]
    assert all(item["company_id"] == 10 for item in ranked)
    assert all(item["cme"] == "cme-research-v1" for item in ranked)


def test_cme_rejects_evidence_from_another_company():
    results = [
        ResearchResult(title="Tenant A", url="https://a.example/a", company_id=101, relevance_score=1),
        ResearchResult(title="Tenant B", url="https://b.example/b", company_id=202, relevance_score=1),
    ]
    ranked = BiteyCME.rank(results, company_id=101)
    assert len(ranked) == 1
    assert ranked[0]["company_id"] == 101
    assert ranked[0]["title"] == "Tenant A"


def test_search_cache_is_tenant_scoped(monkeypatch):
    calls = []

    def fake_memory(company_id, query, limit):
        return {"fresh": False, "results": []}

    def fake_search(query, limit):
        calls.append(query)
        return {
            "provider": "test-provider",
            "results": [{
                "url": f"https://example.org/{len(calls)}",
                "title": f"Evidence {len(calls)}",
                "snippet": query,
            }],
        }

    monkeypatch.setattr(web_intelligence, "search_memory", fake_memory)
    monkeypatch.setattr(web_intelligence, "bitey_search", fake_search)
    web_intelligence._CACHE.clear()

    first = web_intelligence.search_web("same research question", company_id=101)
    second = web_intelligence.search_web("same research question", company_id=202)
    first_again = web_intelligence.search_web("same research question", company_id=101)

    assert first["company_id"] == 101
    assert second["company_id"] == 202
    assert first["results"][0]["company_id"] == 101
    assert second["results"][0]["company_id"] == 202
    assert first["results"][0]["url"] != second["results"][0]["url"]
    assert first_again["cache_hit"] is True
    assert len(calls) == 2


def test_search_results_are_ranked_by_cme(monkeypatch):
    monkeypatch.setattr(web_intelligence, "search_memory", lambda company_id, query, limit: {"fresh": False, "results": []})
    monkeypatch.setattr(
        web_intelligence,
        "bitey_search",
        lambda query, limit: {
            "provider": "test-provider",
            "results": [
                {"url": "https://weak.example/item", "title": "Unrelated", "snippet": "other words"},
                {"url": "https://strong.example/item", "title": "Python deployment guide", "snippet": "Python deployment guide for current applications"},
            ],
        },
    )
    web_intelligence._CACHE.clear()
    response = web_intelligence.search_web("Python deployment guide", company_id=303)
    assert response["cme"] == "cme-research-v1"
    assert response["results"][0]["title"] == "Python deployment guide"
    assert "rank_score" in response["results"][0]
