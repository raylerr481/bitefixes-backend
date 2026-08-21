import pytest

from app.ai.company_intelligence import (
    build_company_profile,
    build_conversation_context,
    normalize_source,
)


def test_company_profile_combines_independent_ai_findings_without_inventing_facts():
    profile = build_company_profile(
        company_id=1,
        sources=[
            {"source_type": "website", "uri": "https://www.bitefixes.com"},
            {"source_type": "pdf", "name": "service-catalog.pdf"},
        ],
        analyses=[
            {
                "provider": "groq",
                "company_name": "BiteFixes",
                "industry": "IT services",
                "services": ["computer repair", "CCTV"],
                "facts": ["Provides technical support"],
            },
            {
                "provider": "deepseek-free",
                "company_name": "BiteFixes",
                "services": ["computer repair", "CCTV"],
                "capabilities": ["remote support"],
            },
        ],
    )
    assert profile["company_id"] == 1
    assert profile["company_name"] == "BiteFixes"
    assert "computer repair" in profile["services"]
    assert "remote support" in profile["capabilities"]
    assert {"groq", "deepseek-free"} == set(profile["analyst_providers"])
    assert len(profile["sources"]) == 2


def test_source_types_are_explicit_and_unknown_sources_are_rejected():
    assert normalize_source({"source_type": "database"})["source_type"] == "database"
    with pytest.raises(ValueError, match="unsupported_company_source"):
        normalize_source({"source_type": "random_system"})


def test_conversation_context_is_company_scoped_and_contains_service_customer_history():
    result = build_conversation_context(
        company_context={
            "profile": {"company_id": 1, "company_name": "BiteFixes"},
            "knowledge": [{"content": "CCTV installation"}],
        },
        conversation={
            "customer": {"id": 7},
            "service": {"key": "cctv_installation"},
            "message": "Minha câmera não funciona",
            "history": [{"role": "user", "content": "Instalei ontem"}],
            "active_ticket": None,
        },
    )
    assert result["company"]["company_id"] == 1
    assert result["service"]["key"] == "cctv_installation"
    assert result["customer"]["id"] == 7
    assert result["company_knowledge"][0]["content"] == "CCTV installation"
