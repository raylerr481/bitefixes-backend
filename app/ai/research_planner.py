"""Plan targeted knowledge acquisition instead of issuing blind searches."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class ResearchPlan:
    question: str
    objectives: List[str] = field(default_factory=list)
    required_evidence: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=lambda: ["internal_knowledge"])


class ResearchPlanner:
    def plan(self, problem: str, known_facts: dict | None = None) -> ResearchPlan:
        facts = known_facts or {}
        objectives = ["identify plausible causes", "find diagnostic tests", "find safe remediation"]
        evidence = []
        if "mobile" in problem:
            evidence = ["device_power", "screen_state", "touch_state", "charging_state"]
        elif "network" in problem or "wifi" in problem:
            evidence = ["adapter_visible", "driver_status", "ip_configuration", "connectivity"]
        elif "notebook" in problem or "computer" in problem:
            evidence = ["memory", "storage", "cpu_load", "temperature", "startup_processes"]
        else:
            evidence = ["symptoms", "environment", "recent_changes", "reproducibility"]
        return ResearchPlan(
            question=problem,
            objectives=objectives,
            required_evidence=[x for x in evidence if x not in facts],
            sources=["internal_knowledge", "approved_search", "trusted_ai_specialist"],
        )
