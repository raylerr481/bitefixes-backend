"""Small in-process knowledge graph abstraction with provenance and confidence."""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class KnowledgeNode:
    key: str
    value: str
    confidence: float
    status: str = "candidate"
    sources: List[str] = field(default_factory=list)
    successes: int = 0
    failures: int = 0


class KnowledgeGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, KnowledgeNode] = {}

    def propose(self, key: str, value: str, source: str, confidence: float = 0.0) -> KnowledgeNode:
        node = self.nodes.get(key)
        if node is None:
            node = KnowledgeNode(key=key, value=value, confidence=max(0.0, min(1.0, confidence)))
            self.nodes[key] = node
        if source not in node.sources:
            node.sources.append(source)
        node.confidence = max(node.confidence, confidence)
        return node

    def record_verification(self, key: str, success: bool) -> KnowledgeNode | None:
        node = self.nodes.get(key)
        if node is None:
            return None
        if success:
            node.successes += 1
            node.confidence = min(1.0, node.confidence + 0.20)
        else:
            node.failures += 1
            node.confidence = max(0.0, node.confidence - 0.20)
        node.status = "trusted" if node.successes >= 2 and node.confidence >= 0.80 else "candidate"
        if node.failures >= 2 and node.confidence < 0.50:
            node.status = "rejected"
        return node
