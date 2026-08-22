from app.services import company_people_service


def test_company_people_context_hides_contact_details():
    monkey = None

    original_list = company_people_service.list_company_people
    company_people_service.list_company_people = lambda company_id, active_only=True: [
        {
            "id": 10,
            "full_name": "Ana Silva",
            "job_title": "Technical Manager",
            "department": "Operations",
            "person_type": "employee",
            "roles": [
                {
                    "role_code": "technical_lead",
                    "role_name": "Technical Lead",
                    "is_primary": True,
                    "authority_level": 60,
                }
            ],
            "is_primary": True,
            "ai_context_authority": True,
            "can_be_contacted_by_ai": True,
            "preferred_language": "pt-BR",
            "preferred_channel": "whatsapp",
            "phone": "+5511999999999",
            "email": "ana@example.com",
        }
    ]

    try:
        context = company_people_service.build_company_people_context(1)
    finally:
        company_people_service.list_company_people = original_list

    assert context["count"] == 1
    person = context["company_people"][0]
    assert person["name"] == "Ana Silva"
    assert person["roles"][0]["code"] == "technical_lead"
    assert "phone" not in person
    assert "email" not in person


def test_unknown_role_is_rejected():
    assert company_people_service.find_company_people_by_role(1, "not_a_real_role") == []
