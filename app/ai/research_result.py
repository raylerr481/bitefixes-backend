"""Generic research evidence contract used by Bitey's Cognitive Mediation Engine.

The contract is domain-neutral: no tenant, product, service, or business rule is
encoded here. Tenant identity is carried as data so callers can enforce isolation.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _clamp(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class ResearchResult:
    """Normalized evidence item produced by research, before ranking."""

    title: str
    url: str
    snippet: str = ""
    content: str = ""
    domain: str = ""
    company_id: Optional[int] = None
    relevance_score: float = 0.0
    authority_score: float = 0.0
    verification_score: float = 0.0
    freshness_score: float = 1.0
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def normalized(self) -> "ResearchResult":
        return ResearchResult(
            title=str(self.title or "").strip(),
            url=str(self.url or "").strip(),
            snippet=str(self.snippet or "").strip()[:2500],
            content=str(self.content or "").strip()[:12000],
            domain=str(self.domain or "").strip().lower(),
            company_id=int(self.company_id) if self.company_id is not None else None,
            relevance_score=_clamp(self.relevance_score),
            authority_score=_clamp(self.authority_score),
            verification_score=_clamp(self.verification_score),
            freshness_score=_clamp(self.freshness_score, 1.0),
            retrieved_at=str(self.retrieved_at),
            metadata=dict(self.metadata or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self.normalized())
