from app.channels.registry import get_adapter, supported_channels


def test_channel_registry_contains_core_channels():
    assert {"whatsapp", "telegram", "messenger"}.issubset(set(supported_channels()))


def test_whatsapp_cloud_payload_normalizes():
    normalize, _ = get_adapter("whatsapp")
    event = normalize({
        "entry": [{"changes": [{"value": {
            "contacts": [{"wa_id": "5511999999999", "profile": {"name": "Ana"}}],
            "messages": [{"id": "wamid.test", "from": "5511999999999", "text": {"body": "Hola Bitey"}}]
        }}]}]
    }, company_id=7)
    assert event is not None
    assert event.request.message == "Hola Bitey"
    assert event.request.channel == "whatsapp"
    assert event.request.company_id == 7
    assert event.request.phone == "5511999999999"


def test_telegram_payload_normalizes():
    normalize, _ = get_adapter("telegram")
    event = normalize({
        "message": {"message_id": 10, "from": {"id": 44, "first_name": "Ana"},
                     "chat": {"id": 44}, "text": "Necesito ayuda"}
    }, company_id=3)
    assert event.request.message == "Necesito ayuda"
    assert event.request.conversation_id == "44"
    assert event.request.company_id == 3


def test_messenger_payload_normalizes():
    normalize, _ = get_adapter("messenger")
    event = normalize({
        "entry": [{"messaging": [{"sender": {"id": "psid-1"},
                                     "message": {"mid": "m1", "text": "Hola"}}]}]
    }, company_id=5)
    assert event.request.message == "Hola"
    assert event.request.conversation_id == "psid-1"
    assert event.request.company_id == 5
