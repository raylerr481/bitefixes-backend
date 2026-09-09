from app.services.bitey_gateway import (
    SUPPORTED_CHANNELS,
    _CONTEXT_RESET_RE,
    _channel_identity,
    _extract_pending_turn,
    _public_result,
    normalize_channel,
)


def test_supported_channels_are_normalized_without_cross_channel_fallback():
    for channel in SUPPORTED_CHANNELS:
        assert normalize_channel(channel.upper()) == channel
    assert normalize_channel("unknown-channel") == "api"


def test_channel_identities_are_isolated():
    assert _channel_identity("website", "", "abc") == ("web:abc", "abc")
    assert _channel_identity("telegram", "123", "abc") == ("telegram:123", "123")
    assert _channel_identity("messenger", "123", "abc") == ("messenger:123", "123")
    assert _channel_identity("whatsapp", "123", "abc") == ("123", "123")
    assert _channel_identity("telegram", "123", "abc") != _channel_identity("messenger", "123", "abc")


def test_reset_phrases_are_explicit_and_do_not_match_normal_messages():
    reset_messages = [
        "Hola",
        "Hola Bitey",
        "prueba de conexión multicanal",
        "Hola, prueba Telegram",
        "prueba WhatsApp",
        "nuevo problema",
        "otra consulta",
        "empecemos de nuevo",
    ]
    for message in reset_messages:
        assert _CONTEXT_RESET_RE.match(message)

    assert not _CONTEXT_RESET_RE.match("Mi PC está lenta")
    assert not _CONTEXT_RESET_RE.match("La conexión está fallando")


def test_pending_turn_extracts_model_question_and_options():
    pending = _extract_pending_turn(
        "¿Cuál es el modelo exacto?\n1. Redmi 9A\n2. Redmi 10\n"
    )
    assert pending["field"] == "model"
    assert pending["question"] == "¿Cuál es el modelo exacto?"
    assert [item["number"] for item in pending["options"]] == [1, 2]


def test_pending_turn_extracts_device_question():
    pending = _extract_pending_turn("¿Qué dispositivo necesitas revisar?")
    assert pending["field"] == "device"


def test_public_result_removes_internal_fields_and_keeps_contract():
    result = _public_result(
        {
            "response": "OK",
            "intent": "diagnostic",
            "confidence": 0.9,
            "gateway_debug": {"x": 1},
            "gateway": {"internal": True},
            "metadata": {"secret": True},
        }
    )
    assert result["response"] == "OK"
    assert result["public_contract"] == "bitey-chat-v1"
    assert "intent" not in result
    assert "confidence" not in result
    assert "gateway_debug" not in result
    assert "gateway" not in result
    assert "metadata" not in result
