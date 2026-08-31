"""End-to-end contract tests for CME continuity across independent tenants.

The same cognitive mechanism must handle different companies without copying
facts, evidence, or ranking state between them.
"""
from app.ai.cme_research import BiteyCME
from app.ai.research_result import ResearchResult


def _evidence(company_id, title, url, query, relevance):
    return ResearchResult(
        title=title,
        url=url,
        snippet=f"Evidence for {query} belonging only to company {company_id}",
        content=f"company_marker={company_id}; query={query}",
        domain=url.split('/')[2],
        company_id=company_id,
        relevance_score=relevance,
        authority_score=0.8,
        verification_score=0.8,
        freshness_score=1.0,
    )


def test_same_cme_handles_two_companies_without_context_contamination():
    query = "diagnose network connectivity"
    company_a = [_evidence(1001, "Company A network guide", "https://a.example/guide", query, 0.95)]
    company_b = [_evidence(2002, "Company B network guide", "https://b.example/guide", query, 0.95)]

    ranked_a = BiteyCME.rank(company_a, company_id=1001)
    ranked_b = BiteyCME.rank(company_b, company_id=2002)

    assert ranked_a[0]["company_id"] == 1001
    assert ranked_b[0]["company_id"] == 2002
    assert "Company B" not in ranked_a[0]["content"]
    assert "Company A" not in ranked_b[0]["content"]
    assert ranked_a[0]["cme"] == ranked_b[0]["cme"] == "cme-research-v1"


def test_cme_drops_foreign_evidence_even_when_mixed_input():
    mixed = [
        _evidence(3003, "Tenant C", "https://c.example/item", "same question", 0.9),
        _evidence(4004, "Tenant D", "https://d.example/item", "same question", 1.0),
    ]
    ranked = BiteyCME.rank(mixed, company_id=3003)
    assert len(ranked) == 1
    assert ranked[0]["company_id"] == 3003
    assert ranked[0]["title"] == "Tenant C"


def test_cme_ranking_is_deterministic_for_same_tenant():
    evidence = [
        _evidence(5005, "Second", "https://b.example/2", "q", 0.7),
        _evidence(5005, "First", "https://a.example/1", "q", 0.7),
    ]
    first = BiteyCME.rank(evidence, company_id=5005)
    second = BiteyCME.rank(evidence, company_id=5005)
    assert [(x["title"], x["rank_score"]) for x in first] == [(x["title"], x["rank_score"]) for x in second]
