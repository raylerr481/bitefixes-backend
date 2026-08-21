"""Teacher/student loop: external models teach candidates; Bitey verifies outcomes."""
from typing import Any, Dict
from app.ai.learning_engine import LearningEngine
from app.ai.experience_memory import ExperienceMemory, Experience


class TeacherLoop:
    def __init__(self, learning: LearningEngine | None = None, memory: ExperienceMemory | None = None) -> None:
        self.learning = learning or LearningEngine()
        self.memory = memory or ExperienceMemory()

    def learn_from_teacher(self, key: str, proposal: str, teacher: str, confidence: float = 0.0):
        return self.learning.ingest_candidate(key, proposal, teacher, confidence)

    def record_case(self, case_id: str, problem: str, symptoms: list[str], action: str, outcome: str, success: bool, confidence: float = 0.5, facts: Dict[str, Any] | None = None):
        experience = Experience(case_id, problem, symptoms, facts or {}, action, outcome, success, "case", confidence)
        self.memory.record(experience)
        return self.memory.similar(problem, symptoms)

    def verify_candidate(self, key: str, success: bool):
        return self.learning.verify(key, success)
