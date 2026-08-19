from app.routers.webhooks import normalize_event


def test_whatsapp_message_is_normalized_for_bitey():
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "contacts": [{"wa_id": "5511999999999", "profile": {"name": "Rayler"}}],
                    "messages": [{"from": "5511999999999", "id": "wamid.TEST", "text": {"body": "Tengo un teléfono con la pantalla rota"}}],
                }
            }]
        }]
    }
    event = normalize_event("whatsapp", payload)
    assert event["channel"] == "whatsapp"
    assert event["phone"] == "5511999999999"
    assert event["customer_name"] == "Rayler"
    assert event["message"] == "Tengo un teléfono con la pantalla rota"
    assert event["conversation_id"] == "5511999999999"


def test_whatsapp_non_text_event_is_ignored():
    payload = {"entry": [{"changes": [{"value": {"messages": [{"from": "5511999999999", "type": "image"}]}}]}]}
    assert normalize_event("whatsapp", payload) is None
