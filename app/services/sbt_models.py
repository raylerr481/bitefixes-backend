"""Domain models for Bitey SBT (Signal & Business Trading intelligence).

SBT is an analysis module of Bitey IA, not a separate brain or execution venue.
It converts verified/weighted market information into an auditable scenario.
No live order execution is performed here.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Direction(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class Evidence:
    source: str
    title: str
    published_at: str | None = None
    reliability: float = 0.5
    url: str | None = None
    sentiment: Direction = Direction.NEUTRAL
    affected_assets: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass
class ImpactNode:
    asset: str
    direction: Direction
    impact_score: float
    horizon: str
    reasons: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class SBTScenario:
    headline: str
    event_type: str
    confidence: float
    horizon: str
    primary_direction: Direction
    impact_chain: list[ImpactNode]
    evidence: list[Evidence]
    risks: list[str] = field(default_factory=list)
    invalidation_conditions: list[str] = field(default_factory=list)
    execution_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
