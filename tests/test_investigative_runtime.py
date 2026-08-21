from app.ai.investigative_runtime import InvestigativeRuntime
from app.ai.trust_engine import TrustEngine


def test_mobile_investigation_requires_evidence():
    result = InvestigativeRuntime().analyze("mobile_repair", {"screen_state": "broken"})
    assert result["status"] == "diagnostic_pending"
    assert "device_power" in result["required_evidence"]


def test_trust_requires_verification_and_corroboration():
    result = TrustEngine().evaluate({"claim": "test"}, verified=True, corroborations=1)
    assert result["status"] == "candidate"
    result = TrustEngine().evaluate({"claim": "test"}, verified=True, corroborations=2)
    assert result["status"] == "trusted"
