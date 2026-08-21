"""Trust policy for promoting candidate knowledge.

External AI output is evidence at most, never authority. Promotion requires
verification plus sufficiently independent corroboration and source quality.
"""
from typing import Any, Dict, Iterable

SOURCE_WEIGHTS = {
    "official_documentation": 1.00,
    "primary_source": 1.00,
    "technical_documentation": 0.90,
    "reputable_secondary": 0.75,
    "approved_search": 0.55,
    "trusted_ai_specialist": 0.30,
    "ai": 0.25,
}


class TrustEngine:
    def evaluate(self, candidate: Dict[str, Any], *, verified: bool,
                 corroborations: int = 0, sources: Iterable[Dict[str, Any]] | None = None,
                 conflicts: int = 0) -> Dict[str, Any]:
        source_items = list(sources or [])
        if source_items:
            unique_source_types = {str(s.get("type", "unknown")) for s in source_items}
            independent = max(0, min(corroborations, len(unique_source_types)))
            source_quality = max(SOURCE_WEIGHTS.get(str(s.get("type")), 0.40) for s in source_items)
        else:
            independent = max(0, corroborations)
            source_quality = 0.75 if independent >= 2 else 0.25
        score = 0.20 + 0.30 * source_quality
        score += min(0.25, 0.125 * independent)
        score += 0.25 if verified else 0.0
        score -= min(0.30, 0.15 * max(0, conflicts))
        score = max(0.0, min(1.0, score))
        promotable = bool(verified and independent >= 2 and conflicts == 0
                          and score >= 0.80 and source_quality >= 0.75)
        return {
            "trust_score": score,
            "status": "trusted" if promotable else "candidate",
            "promotable": promotable,
            "independent_corroborations": independent,
            "source_quality": source_quality,
            "candidate": candidate,
        }
