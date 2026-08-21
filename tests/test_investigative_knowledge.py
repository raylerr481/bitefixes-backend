from app.ai.research_planner import ResearchPlanner
from app.ai.hypothesis_engine import HypothesisEngine
from app.ai.verification_engine import VerificationEngine
from app.ai.learning_engine import LearningEngine


def test_research_plan_is_targeted():
    plan = ResearchPlanner().plan("mobile_repair", {"device_power": True})
    assert "device_power" not in plan.required_evidence
    assert "screen_state" in plan.required_evidence


def test_failed_evidence_reduces_hypothesis():
    engine = HypothesisEngine()
    ranked = engine.rank([{"name": "screen_damage", "confidence": 0.8}], [{"contradicts": "screen_damage"}])
    assert ranked[0]["confidence"] < 0.8


def test_verification_is_required_for_promotion():
    verifier = VerificationEngine()
    assert not verifier.verify(True, "single observation", 0.5).promotable
    assert verifier.verify(True, "verified result", 0.8).promotable


def test_learning_does_not_trust_candidate_immediately():
    learning = LearningEngine()
    node = learning.ingest_candidate("wifi_driver", "reinstall driver", "groq", 0.95)
    assert node.status == "candidate"
    learning.verify("wifi_driver", True)
    assert learning.graph.nodes["wifi_driver"].status == "candidate"
    learning.verify("wifi_driver", True)
    assert learning.graph.nodes["wifi_driver"].status == "trusted"
