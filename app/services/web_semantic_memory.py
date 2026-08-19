"""Semantic memory and evidence graph for Bitey Web Intelligence."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from app.supabase_client import supabase


def _hash_claim(claim: str) -> str:
    return hashlib.sha256((claim or "").strip().lower().encode("utf-8")).hexdigest()


def save_claim(company_id: int, claim: str, document_id: Optional[int] = None,
               confidence_score: float = 0.4, verification_score: float = 0.0,
               status: str = "candidate", embedding: Optional[List[float]] = None) -> Optional[int]:
    claim = (claim or "").strip()
    if not claim:
        return None
    payload: Dict[str, Any] = {
        "company_id": company_id, "document_id": document_id,
        "claim": claim, "claim_hash": _hash_claim(claim),
        "confidence_score": max(0.0, min(1.0, confidence_score)),
        "verification_score": max(0.0, min(1.0, verification_score)),
        "status": status,
    }
    if embedding:
        payload["embedding"] = embedding
    try:
        existing = (supabase.table("web_claims").select("id")
                    .eq("company_id", company_id).eq("claim_hash", payload["claim_hash"])
                    .limit(1).execute())
        if existing.data:
            claim_id = existing.data[0]["id"]
            supabase.table("web_claims").update(payload).eq("id", claim_id).execute()
            return claim_id
        created = supabase.table("web_claims").insert(payload).execute()
        return created.data[0]["id"] if created.data else None
    except Exception as error:
        print("[WEB CLAIM WARNING]", error)
        return None


def search_claims(company_id: int, query: str, limit: int = 8) -> List[Dict[str, Any]]:
    try:
        result = supabase.rpc("search_bitey_web_claims", {
            "p_company_id": company_id, "p_query": query,
            "p_limit": max(1, min(limit, 20)), "p_min_confidence": 0.35,
        }).execute()
        return result.data or []
    except Exception as error:
        print("[WEB CLAIM SEARCH WARNING]", error)
        return []


def relate_claims(company_id: int, source_claim_id: int, target_claim_id: int,
                  relation_type: str, confidence_score: float = 0.5,
                  evidence_count: int = 1) -> bool:
    if source_claim_id == target_claim_id:
        return False
    try:
        supabase.table("web_claim_relations").upsert({
            "company_id": company_id,
            "source_claim_id": source_claim_id,
            "target_claim_id": target_claim_id,
            "relation_type": relation_type,
            "confidence_score": max(0.0, min(1.0, confidence_score)),
            "evidence_count": max(1, evidence_count),
        }, on_conflict="source_claim_id,target_claim_id,relation_type").execute()
        return True
    except Exception as error:
        print("[WEB CLAIM RELATION WARNING]", error)
        return False


def record_feedback(company_id: int, query: str, outcome: str,
                    usefulness_score: float, customer_id: Optional[int] = None,
                    document_id: Optional[int] = None, claim_id: Optional[int] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
    try:
        supabase.table("web_memory_feedback").insert({
            "company_id": company_id, "customer_id": customer_id,
            "document_id": document_id, "claim_id": claim_id,
            "query": query, "outcome": outcome,
            "usefulness_score": max(0.0, min(1.0, usefulness_score)),
            "metadata": metadata or {},
        }).execute()
        return True
    except Exception as error:
        print("[WEB MEMORY FEEDBACK WARNING]", error)
        return False


def health(company_id: int) -> Dict[str, Any]:
    try:
        result = supabase.rpc("bitey_web_memory_health", {"p_company_id": company_id}).execute()
        return result.data or {}
    except Exception as error:
        return {"error": str(error)}
