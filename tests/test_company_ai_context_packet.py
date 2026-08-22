from app.ai.ai_council import _business_index


def test_company_ai_profile_objectives_and_directives_are_carried_in_bounded_index():
    packet = _business_index({
        "company": {"name": "BiteFixes"},
        "company_ai_profile": {
            "company_id": 1,
            "company_name": "BiteFixes",
            "description": "IT services",
            "industry": "technology",
            "profile": {"customers": ["businesses"]},
            "objectives": ["resolve customer issues quickly"],
            "directives": {"language": "customer language", "tone": "clear"},
            "authoritative": True,
            "internal_secret": "must-not-be-forwarded",
        },
        "services": [{"name": "Computer Repair"}],
    })

    profile = packet["company_ai_profile"]
    assert profile["company_id"] == 1
    assert profile["objectives"] == ["resolve customer issues quickly"]
    assert profile["directives"]["tone"] == "clear"
    assert "internal_secret" not in profile
