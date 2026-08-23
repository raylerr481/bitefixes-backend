from app.ai.consultation_service import _research_query


def test_short_followup_gets_active_context_anchor():
    query = _research_query(
        "quanto custa?",
        {
            "contextual_state": {
                "active_topic": "upgrade_hardware",
                "active_service": "SSD upgrade",
            }
        },
        "quote",
    )
    assert "SSD upgrade" in query
    assert "quanto custa?" in query


def test_specific_message_is_not_bloated():
    message = "Qual a versão mais recente do Windows 11 para notebooks compatíveis?"
    query = _research_query(
        message,
        {"contextual_state": {"active_topic": "software_update", "active_service": "Windows installation"}},
        "software_update",
    )
    assert query == message
