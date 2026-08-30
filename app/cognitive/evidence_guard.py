"""Evidence boundary for Bitey's cognitive state.

The LLM may propose hypotheses, interpretations, and candidates, but only
observed/user-provided/retrieved evidence may become canonical facts.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

FACT_SOURCES = {"user", "system", "database", "search", "tool", "verified"}
HYPOTHESIS_SOURCES = {"llm", "inference", "candidate", "ai_council"}



def normalize_evidence(items: Iterable[Any]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for item in items or []:
        if isinstance(item, str):
            normalized.append({"content": item, "source": "unknown", "verified": False})
        elif isinstance(item, dict):
            normalized.append(dict(item))
    return normalized



def partition_claims(claims: Iterable[Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Separate grounded facts from hypotheses without discarding candidates."""
    facts: List[Dict[str, Any]] = []
    hypotheses: List[Dict[str, Any]] = []
    for claim in normalize_evidence(claims):
        source = str(claim.get("source", "unknown")).lower()
        verified = bool(claim.get("verified", False))
        if verified or source in FACT_SOURCES:
            claim["status"] = "fact"
            facts.append(claim)
        elif source in HYPOTHESIS_SOURCES or claim.get("hypothesis") is True:
            claim["status"] = "hypothesis"
            hypotheses.append(claim)
        else:
            claim["status"] = "unverified"
            hypotheses.append(claim)
    return {"facts": facts, "hypotheses": hypotheses}



def guard_state_update(current: Dict[str, Any], proposed: Dict[str, Any], evidence: Iterable[Any] = ()) -> Dict[str, Any]:
    """Apply a proposal while allowing canonical changes only when grounded."""
    current = dict(current or {})
    proposed = dict(proposed or {})
    partitioned = partition_claims(evidence)
    grounded_keys = {
        str(item.get("key"))
        for item in partitioned["facts"]
        if item.get("key")
    }

    result = dict(current)
    for key, value in proposed.items():
        # Reasoning artifacts are explicitly non-canonical.
        if key in {"hypotheses", "interpretation", "reasoning", "candidates"}:
            result[key] = value
            continue
        # A factual field may change only when evidence explicitly grounds it.
        if key in grounded_keys:
            result[key] = value
            continue
        # Everything else is rejected as an unsupported state mutation.
        continue

    result["evidence"] = partitioned["facts"]
    result["hypotheses"] = partitioned["hypotheses"] + list(result.get("hypotheses") or [])
    return result
