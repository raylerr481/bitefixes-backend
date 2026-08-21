from app.ai.problem_analyzer import ProblemAnalyzer
from app.ai.evidence_engine import EvidenceEngine
from app.ai.solution_engine import SolutionEngine


def test_problem_state_preserves_multiturn_facts():
    analyzer = ProblemAnalyzer()
    state = analyzer.start("mobile_repair")
    analyzer.add_symptom(state, "screen_damage")
    analyzer.add_symptom(state, "screen_damage", touch="unknown")
    assert state.symptoms == ["screen_damage"]
    assert state.problem == "mobile_repair"


def test_evidence_ranks_hypothesis():
    analyzer = ProblemAnalyzer()
    state = analyzer.start("mobile_repair")
    analyzer.add_hypothesis(state, "screen_damage", 0.6)
    analyzer.add_hypothesis(state, "charging_failure", 0.5)
    analyzer.add_evidence(state, "user", "pantalla quebrada", "screen_damage")
    ranked = EvidenceEngine().score(state.hypotheses, state.evidence)
    assert ranked[0]["name"] == "screen_damage"


def test_solution_requires_verification():
    result = SolutionEngine().propose(
        "mobile_repair",
        [{"name": "screen_damage", "confidence": 0.8}],
        [{"source": "user", "observation": "pantalla quebrada", "supports": "screen_damage"}],
    )
    assert result
    assert all(item["requires_verification"] for item in result)
