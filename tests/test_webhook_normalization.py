from app.routers.webhooks import normalize_event


def test_whatsapp_text_event_normalizes():
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "contacts": [{"wa_id": "5511999999999", "profile": {"name": "Rayler"}}],
                    "messages": [{"from": "5511999999999", "id": "wamid.1", "type": "text", "text": {"body": "Hola Bitey"}}],
                }
            }]
        }]
    }
    event = normalize_event("whatsapp", payload)
    assert event["message"] == "Hola Bitey"
    assert event["phone"] == "5511999999999"
    assert event["customer_name"] == "Rayler"
    assert event["conversation_id"] == "5511999999999"


def test_telegram_text_event_normalizes():
    payload = {"message": {"message_id": 7, "chat": {"id": 12345}, "from": {"first_name": "Rayler", "last_name": "R"}, "text": "Hola Bitey"}}
    event = normalize_event("telegram", payload)
    assert event["message"] == "Hola Bitey"
    assert event["conversation_id"] == "12345"
    assert event["customer_name"] == "Rayler"


def test_messenger_text_event_normalizes():
    payload = {"entry": [{"messaging": [{"sender": {"id": "psid-1"}, "message": {"text": "Hola Bitey"}}]}]}
    event = normalize_event("messenger", payload)
    assert event["message"] == "Hola Bitey"
    assert event["conversation_id"] == "psid-1"


def test_non_text_events_are_ignored():
    assert normalize_event("whatsapp", {"entry": [{"changes": [{"value": {"messages": [{"type": "image"}]}}]}]}) is None
