from app.ai.ai_council import _business_index


def test_business_index_includes_verified_company_location_without_guessing():
    context = {
        "company_id": 1,
        "company": {"id": 1, "name": "BiteFixes"},
        "locations": [
            {
                "id": 1,
                "name": "BiteFixes - Sede principal",
                "location_type": "headquarters",
                "street": "Rua Garibaldi",
                "number": "194",
                "city": "Esteio",
                "state": "RS",
                "country": "Brasil",
                "maps_url": None,
                "phone": None,
                "whatsapp": None,
                "opening_hours": {},
                "appointment_required": False,
                "is_primary": True,
            }
        ],
    }

    packet = _business_index(context)
    location = packet["locations"][0]

    assert location["name"] == "BiteFixes - Sede principal"
    assert location["street"] == "Rua Garibaldi"
    assert location["number"] == "194"
    assert location["city"] == "Esteio"
    assert location["state"] == "RS"
    assert location["country"] == "Brasil"
    assert location["maps_url"] is None


def test_followup_messages_retain_location_topic():
    previous = {
        "active_topic": "company_location",
        "active_object": "BiteFixes workshop",
        "active_service": "mobile_repair",
    }
    followups = [
        "revisa ahora si tienes direccion",
        "no tienes la direccion el taller?",
        "se puede ir para cambiar la pantalla?",
    ]

    assert previous["active_topic"] == "company_location"
    assert previous["active_object"] == "BiteFixes workshop"
    assert previous["active_service"] == "mobile_repair"
    assert all(isinstance(text, str) and text for text in followups)
