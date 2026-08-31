"""Bitey Cognitive Mediation Engine (CME) research ranking.

CME ranks evidence, not business-specific answers. It uses only evidence
signals supplied by the research layer and therefore remains reusable across
companies and domains.
"""
from __future__ import annotations

from typing import Any, Iterable, List, Dict, Optional
from .research_result import ResearchResult


class BiteyCME:
    """Small deterministic mediation stage for normalized research evidence."""

    VERSION = "cme-research-v1"

    @staticmethod
    def rank(results: Iterable[ResearchResult], *, company_id: Optional[int] = None,
             limit: int = 8) -> List[Dict[str, Any]]:
        normalized: List[ResearchResult] = []
        for result in results:
            item = result.normalized()
            if company_id is not None and item.company_id != company_id:
                continue
            normalized.append(item)

        # Domain-neutral evidence weighting. No company/service/product rules.
        ranked: List[Dict[str, Any]] = []
        for item in normalized:
            score = (
                item.relevance_score * 0.40
                + item.authority_score * 0.25
                + item.verification_score * 0.25
                + item.freshness_score * 0.10
            )
            payload = item.to_dict()
            payload["rank_score"] = round(max(0.0, min(1.0, score)), 4)
            payload["ranking_signals"] = {
                "relevance": item.relevance_score,
                "authority": item.authority_score,
                "verification": item.verification_score,
                "freshness": item.freshness_score,
            }
            payload["cme"] = self_name()
            ranked.append(payload)

        ranked.sort(key=lambda row: (-row["rank_score"], row["url"]))
        return ranked[: max(1, int(limit))]


def self_name() -> str:
    return BiteyCME.VERSION
