from app.ai.comparative_engine import compare_answers


def test_core_wins_when_confident():
    result = compare_answers(
        message="mi notebook esta lento",
        intent="hardware_upgrade",
        core_confidence=0.92,
        candidates=[
            {"source": "core", "answer": "Puedo ayudarte a diagnosticar el rendimiento del notebook.", "intent": "hardware_upgrade", "authority": 1.0, "safety": 1.0},
            {"source": "external", "answer": "Podrías revisar memoria y almacenamiento.", "intent": "hardware_upgrade", "authority": 0.45, "safety": 0.85},
        ],
    )
    assert result["selected_source"] == "core"


def test_core_remains_authoritative_when_external_does_not_materially_outrank_it():
    result = compare_answers(
        message="quiero entender por que una red wifi empresarial pierde conexion cada cierto tiempo",
        intent="network_configuration",
        core_confidence=0.20,
        candidates=[
            {"source": "core", "answer": "Voy a ayudarte.", "intent": "network_configuration", "authority": 1.0, "safety": 1.0},
            {"source": "external", "answer": "Conviene revisar interferencias, canales, roaming, DHCP y saturacion del punto de acceso.", "intent": "network_configuration", "authority": 0.45, "safety": 0.85, "provider": "free"},
        ],
    )
    assert result["selected_source"] == "core"
    assert result["reason"] == "core_authoritative"
