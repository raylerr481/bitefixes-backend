from app.ai.contextual_opportunity_engine import build_ai_guidance, build_opportunities, detect_signals


def _state():
    return {
        "company": {"id": "bitefixes", "name": "BiteFixes"},
        "available_services": [
            {"id": "mobile_repair", "name": "Mobile phone repair"},
            {"id": "cctv", "name": "CCTV installation"},
        ],
        "capabilities": ["screen replacement", "home service", "workshop service"],
        "conversation": {
            "active_topic": "mobile repair",
            "active_object": "mobile phone",
            "active_model": "Redmi 9A",
            "active_problem": "broken screen",
            "active_service": "mobile_repair",
        },
    }


def test_detects_business_opportunity_signal():
    signals = detect_signals("quiero reparar la pantalla de mi movil", _state())
    assert any(s["signal_type"] == "SERVICE_REQUEST" for s in signals)


def test_builds_non_blocking_business_opportunity():
    signals = detect_signals("¿donde puedo llevarlo?", _state())
    opportunities = build_opportunities(signals, _state())
    assert any(o["opportunity_type"] == "BUSINESS_CAPABILITY_MATCH" for o in opportunities)
    guidance = build_ai_guidance(opportunities)
    assert "not a command" in guidance
    assert "BiteFixes" in guidance


def test_contextual_layer_does_not_require_service_mapping():
    state = _state()
    state["available_services"] = []
    state["capabilities"] = ["technical support"]
    signals = detect_signals("necesito ayuda", state)
    opportunities = build_opportunities(signals, state)
    assert isinstance(opportunities, list)
