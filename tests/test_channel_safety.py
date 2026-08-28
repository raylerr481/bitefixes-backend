import asyncio

from app.services.channel_safety import channel_mode, delivery_decision, live_enabled
from app.services.outbound_channel_adapter import send_external_response


def test_managed_channels_default_to_mock_and_fail_closed(monkeypatch):
    for channel in ("whatsapp", "telegram", "messenger"):
        monkeypatch.delenv(f"{channel.upper()}_MODE", raising=False)
        monkeypatch.delenv(f"{channel.upper()}_LIVE", raising=False)
        assert channel_mode(channel) == "mock"
        assert live_enabled(channel) is False
        decision = delivery_decision(channel)
        assert decision["allowed"] is False
        assert decision["reason"] == "zero_cost_fail_closed"


def test_live_requires_both_mode_and_explicit_flag(monkeypatch):
    monkeypatch.setenv("WHATSAPP_MODE", "live")
    monkeypatch.setenv("WHATSAPP_LIVE", "true")
    assert live_enabled("whatsapp") is True
    assert delivery_decision("whatsapp")["allowed"] is True

    monkeypatch.setenv("WHATSAPP_LIVE", "false")
    assert live_enabled("whatsapp") is False


def test_mock_delivery_never_calls_provider(monkeypatch):
    monkeypatch.setenv("WHATSAPP_MODE", "mock")
    monkeypatch.setenv("WHATSAPP_LIVE", "false")

    async def fail_if_called(*args, **kwargs):
        raise AssertionError("provider call made in mock mode")

    monkeypatch.setattr("app.services.outbound_channel_adapter._post_json", fail_if_called)
    result = asyncio.run(send_external_response(
        channel="whatsapp",
        response="Hola desde Bitey",
        event={"external_conversation_id": "5511998664378", "phone": "5511998664378"},
    ))
    assert result["status"] == "mocked"
    assert result["mode"] == "mock"
    assert result["recipient_present"] is True
