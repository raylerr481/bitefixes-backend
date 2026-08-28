"""Deterministic, provider-neutral SBT impact engine.

This first layer does not predict guaranteed profits. It ranks evidence and
builds a possible domino chain for later validation with live market data,
backtests and demo/paper execution.
"""
from __future__ import annotations
from collections import defaultdict
from .sbt_models import Direction, Evidence, ImpactNode, SBTScenario


EVENT_MAP = {
    "oil_supply_disruption": {
        "USOIL": Direction.BULLISH,
        "BRENT": Direction.BULLISH,
        "EURUSD": Direction.BEARISH,
        "USDJPY": Direction.BULLISH,
        "AIRLINES": Direction.BEARISH,
    },
    "shipping_disruption": {
        "BRENT": Direction.BULLISH,
        "USOIL": Direction.BULLISH,
        "AIRLINES": Direction.BEARISH,
        "INDUSTRIALS": Direction.BEARISH,
    },
    "central_bank_hawkish": {
        "USD": Direction.BULLISH,
        "GOLD": Direction.BEARISH,
        "EURUSD": Direction.BEARISH,
        "EQUITIES": Direction.BEARISH,
    },
}


def analyze_event(*, headline: str, event_type: str, evidence: list[Evidence], horizon: str = "intraday") -> SBTScenario:
    weights = defaultdict(float)
    reasons: dict[str, list[str]] = defaultdict(list)
    for item in evidence:
        source_weight = max(0.0, min(1.0, item.reliability))
        sign = 1.0 if item.sentiment == Direction.BULLISH else -1.0 if item.sentiment == Direction.BEARISH else 0.0
        for asset in item.affected_assets:
            weights[asset] += sign * source_weight
            reasons[asset].append(item.source)

    mapped = EVENT_MAP.get(event_type, {})
    for asset, direction in mapped.items():
        if asset not in weights:
            weights[asset] = 0.35 if direction == Direction.BULLISH else -0.35
            reasons[asset].append("event_map")

    nodes: list[ImpactNode] = []
    for asset, score in sorted(weights.items(), key=lambda pair: abs(pair[1]), reverse=True):
        direction = Direction.BULLISH if score > 0 else Direction.BEARISH if score < 0 else Direction.NEUTRAL
        nodes.append(ImpactNode(asset=asset, direction=direction, impact_score=round(min(abs(score), 1.0), 3), horizon=horizon, reasons=reasons[asset], confidence=round(min(abs(score), 1.0), 3)))

    bullish = sum(max(n.impact_score, 0) for n in nodes)
    bearish = sum(max(n.impact_score, 0) for n in nodes if n.direction == Direction.BEARISH)
    primary = Direction.BULLISH if bullish > bearish else Direction.BEARISH if bearish > bullish else Direction.NEUTRAL
    confidence = round(min(1.0, max([n.confidence for n in nodes], default=0.0)), 3)

    return SBTScenario(
        headline=headline,
        event_type=event_type,
        confidence=confidence,
        horizon=horizon,
        primary_direction=primary,
        impact_chain=nodes,
        evidence=evidence,
        risks=["headline reversal", "false or delayed information", "market already priced in"],
        invalidation_conditions=["new evidence contradicts the event", "price action fails to confirm the thesis"],
        execution_allowed=False,
    )
