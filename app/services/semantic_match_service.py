"""Bitey Semantic Match Engine V1.

Resolves user language against the governed semantic graph. This is a safe
baseline: lexical/term matching first, graph expansion second. A future
embedding/vector provider can be added behind the same interface without
changing decision_engine callers.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List

from app.database.supabase import database


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-zA-Z0-9À-ÿ\s_-]", " ", value.lower())
    return re.sub(r"\s+", " ", value).strip()


def match_semantic_context(message: str, company_id: int | None = None, language: str | None = None, limit: int = 12) -> Dict[str, Any]:
    """Return semantic concepts and nearby graph relations relevant to a message."""
    normalized = _normalize(message)
    if not normalized:
        return {"matches": [], "relations": [], "confidence": 0.0, "query": ""}

    tokens = {t for t in normalized.split() if len(t) >= 3}
    terms_result = database.table("semantic_terms").select("concept_id,term,language,scope,company_id,confidence").limit(5000).execute()
    term_rows = terms_result.data or []
    scored: Dict[int, Dict[str, Any]] = {}

    for row in term_rows:
        scope = row.get("scope", "global")
        row_company = row.get("company_id")
        if scope == "company" and row_company != company_id:
            continue
        if language and row.get("language") not in (None, language, language.split("-")[0]):
            continue
        term = _normalize(row.get("term", ""))
        if not term:
            continue
        score = 0.0
        if term in normalized:
            score = 1.0
        else:
            term_tokens = set(term.split())
            if term_tokens:
                overlap = len(tokens & term_tokens) / len(term_tokens)
                score = overlap * 0.75
        score *= float(row.get("confidence") or 0.5)
        if score > scored.get(row["concept_id"], {}).get("score", 0):
            scored[row["concept_id"]] = {"concept_id": row["concept_id"], "matched_term": row.get("term"), "score": score}

    top = sorted(scored.values(), key=lambda x: x["score"], reverse=True)[:limit]
    ids = [x["concept_id"] for x in top]
    concepts = []
    if ids:
        concepts = (database.table("semantic_concepts").select("id,code,name,description,concept_type,scope,company_id,confidence").in_("id", ids).execute()).data or []
    concept_map = {c["id"]: c for c in concepts}
    for item in top:
        item["concept"] = concept_map.get(item["concept_id"])

    relations = []
    if ids:
        relations = (database.table("semantic_relationships").select("subject_id,predicate,object_id,confidence,status,scope").in_("subject_id", ids).eq("status", "approved").limit(100).execute()).data or []

    best = top[0]["score"] if top else 0.0
    return {"query": normalized, "matches": top, "relations": relations, "confidence": min(1.0, best)}
