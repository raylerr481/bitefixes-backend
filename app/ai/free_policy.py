"""Hard zero-cost policy for Bitey's AI model routing.

A provider is eligible only when it is explicitly classified as free. This is
an allow-list policy: unknown or paid providers are never selected.
"""
from __future__ import annotations

import os


FREE_ONLY = os.getenv("BITEY_FREE_ONLY", "true").lower() != "false"


def provider_allowed(cost_class: str) -> bool:
    if not FREE_ONLY:
        return True
    return cost_class.lower() == "free"


def max_estimated_cost() -> float:
    return 0.0 if FREE_ONLY else float(os.getenv("AI_CONSULT_MAX_ESTIMATED_COST", "0.01"))
