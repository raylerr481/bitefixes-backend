"""Provenance records used by Bitey's knowledge acquisition pipeline."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class EvidenceSource:
    type: str
    locator: str = ""
    title: str = ""
    excerpt: str = ""
    retrieved_at: str = ""
    independent_group: str = ""
    supports: bool = True


@dataclass
class KnowledgeClaim:
    claim: str
    sources: List[EvidenceSource] = field(default_factory=list)
    conflicts: int = 0

    def independent_groups(self) -> set[str]:
        return {
            s.independent_group or s.type
            for s in self.sources
            if s.supports
        }

    def has_conflict(self) -> bool:
        return self.conflicts > 0 or any(not s.supports for s in self.sources)
