"""Promote only verified knowledge; external AI suggestions remain candidates."""
from app.ai.knowledge_graph import KnowledgeGraph, KnowledgeNode


class LearningEngine:
    def __init__(self, graph: KnowledgeGraph | None = None) -> None:
        self.graph = graph or KnowledgeGraph()

    def ingest_candidate(self, key: str, value: str, source: str, confidence: float = 0.0) -> KnowledgeNode:
        # External models can propose knowledge, but never promote it directly.
        return self.graph.propose(key, value, source, confidence)

    def verify(self, key: str, success: bool) -> KnowledgeNode | None:
        return self.graph.record_verification(key, success)
