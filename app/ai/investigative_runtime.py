"""Runtime facade for Bitey's investigative knowledge cycle.

This layer is intentionally side-effect free: it plans investigation, ranks
hypotheses and proposes next evidence without creating tickets or promoting
knowledge.
"""
from typing import Any, Dict, List

from app.ai.research_planner import ResearchPlanner
from app.ai.hypothesis_engine import HypothesisEngine
from app.ai.solution_engine import SolutionEngine


class InvestigativeRuntime:
    def __init__(self) -> None:
        self.planner = ResearchPlanner()
        self.hypotheses = HypothesisEngine()
        self.solutions = SolutionEngine()

    def analyze(self, problem: str, facts: Dict[str, Any] | None = None,
                hypotheses: List[Dict[str, Any]] | None = None,
                evidence: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        facts = facts or {}
        hypotheses = hypotheses or []
        evidence = evidence or []
        plan = self.planner.plan(problem, facts)
        ranked = self.hypotheses.rank(hypotheses, evidence)
        solutions = self.solutions.propose(problem, ranked, evidence)
        return {
            "question": plan.question,
            "objectives": plan.objectives,
            "required_evidence": plan.required_evidence,
            "sources": plan.sources,
            "hypotheses": ranked,
            "solutions": solutions,
            "status": "diagnostic_pending" if plan.required_evidence else "ready_for_verification",
        }
