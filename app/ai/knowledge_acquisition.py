"""Governed knowledge acquisition for Bitey.

External sources can produce candidates, never authoritative facts. Promotion is
performed only after corroboration/verification by the trust layer.
"""
from typing import Any, Dict, Iterable


class KnowledgeAcquisition:
    def collect(self, candidates: Iterable[Dict[str, Any]], *, source_policy: str = "approved_only") -> list[Dict[str, Any]]:
        result = []
        for item in candidates or []:
            if not isinstance(item, dict):
                continue
            result.append({
                "claim": str(item.get("claim") or item.get("answer") or "").strip(),
                "source": item.get("source") or "unknown",
                "status": "candidate",
                "source_policy": source_policy,
                "evidence": item.get("evidence") or [],
            })
        return [x for x in result if x["claim"]]
