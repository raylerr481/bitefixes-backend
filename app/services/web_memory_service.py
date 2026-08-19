"""Persistent, freshness-aware Bitey web memory with hybrid retrieval."""
from __future__ import annotations
import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.supabase_client import supabase
from app.services.web_semantic_memory import save_claim

def _normalize_query(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())

def _hash_url(url: str) -> str:
    return hashlib.sha256((url or "").strip().encode("utf-8")).hexdigest()

def _stale(row: Dict[str, Any]) -> bool:
    stamp = row.get("last_verified_at") or row.get("fetched_at")
    if not stamp: return True
    try:
        dt = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        ttl = int(row.get("freshness_ttl_seconds") or 2592000)
        return (datetime.now(timezone.utc) - dt).total_seconds() > ttl
    except Exception: return True

def _extract_claim_candidates(content: str, limit: int = 12) -> List[str]:
    """Conservative, non-LLM claim candidate extraction; candidates never become authoritative knowledge automatically."""
    text = re.sub(r"\s+", " ", content or "").strip()
    if not text: return []
    candidates: List[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        sentence = sentence.strip(" \t\r\n-•")
        low = sentence.casefold()
        if 45 <= len(sentence) <= 500 and not sentence.endswith("?") and not any(x in low for x in ("cookie", "subscribe", "sign in", "privacy policy", "accept all")):
            candidates.append(sentence)
        if len(candidates) >= limit: break
    return candidates

def _persist_claim_candidates(company_id: Optional[int], document_id: Optional[int], content: str, verification_score: float, authority_score: float) -> List[int]:
    if company_id is None or not document_id: return []
    ids: List[int] = []
    confidence = max(0.35, min(0.95, authority_score * 0.45 + verification_score * 0.55))
    for claim in _extract_claim_candidates(content):
        claim_id = save_claim(company_id, claim, document_id=document_id, confidence_score=confidence, verification_score=max(0.0, min(1.0, verification_score)), status="candidate")
        if claim_id: ids.append(claim_id)
    return ids

def record_accesses(company_id: int, customer_id: Optional[int], query: str, rows: List[Dict[str, Any]], method: str = "hybrid", used: bool = True) -> None:
    for row in rows[:20]:
        try:
            relevance = float(row.get("keyword_score") or row.get("relevance_score") or 0)
            authority = float(row.get("authority_score") or 0)
            final = float(row.get("final_score") or row.get("score") or 0)
            supabase.table("web_memory_accesses").insert({"company_id": company_id, "customer_id": customer_id, "document_id": row.get("id"), "query": query, "retrieval_method": method, "relevance_score": max(0, min(1, relevance)), "freshness_score": 1.0 if not _stale(row) else 0.0, "authority_score": max(0, min(1, authority)), "final_score": max(0, min(1, final)), "used_in_answer": bool(used)}).execute()
        except Exception as error: print("[WEB MEMORY ACCESS WARNING]", error)

def search_memory(company_id: int, query: str, limit: int = 5, freshness_required: bool = False) -> Dict[str, Any]:
    normalized = _normalize_query(query)
    if not normalized: return {"found": False, "fresh": False, "stale": False, "results": []}
    try:
        result = supabase.rpc("search_bitey_web_memory_hybrid", {"p_company_id": company_id, "p_query": normalized, "p_limit": max(1, min(limit, 20)), "p_freshness_required": bool(freshness_required)}).execute()
        rows = result.data or []
    except Exception as error: return {"found": False, "fresh": False, "stale": False, "results": [], "error": str(error)}
    fresh_rows = [row for row in rows if not _stale(row)]
    if fresh_rows: record_accesses(company_id, None, normalized, fresh_rows, method="hybrid_memory", used=True)
    return {"found": bool(rows), "fresh": bool(fresh_rows), "stale": bool(rows) and not bool(fresh_rows), "stale_count": len(rows) - len(fresh_rows), "results": fresh_rows, "all_results_count": len(rows), "normalized_query": normalized}

def record_search(company_id: int, query: str, source: str, *, customer_id: Optional[int] = None, cache_hit: bool = False, local_hit_count: int = 0, external_used: bool = False, freshness_required: bool = False, metadata: Optional[Dict[str, Any]] = None) -> None:
    try:
        supabase.table("web_searches").insert({"company_id": company_id, "customer_id": customer_id, "query": query, "normalized_query": _normalize_query(query), "source": source, "cache_hit": cache_hit, "local_hit_count": local_hit_count, "external_used": external_used, "freshness_required": freshness_required, "metadata": metadata or {}}).execute()
    except Exception as error: print("[WEB MEMORY AUDIT WARNING]", error)

def store_document(company_id: Optional[int], item: Dict[str, Any], *, verification_score: float = 0.0, authority_score: float = 0.5, freshness_ttl_seconds: int = 2592000) -> Optional[int]:
    url = str(item.get("url") or item.get("canonical_url") or "").strip()
    if not url: return None
    content = str(item.get("content") or item.get("snippet") or "")
    payload = {"company_id": company_id, "canonical_url": url, "url_hash": _hash_url(url), "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(), "title": item.get("title"), "source_domain": item.get("source_domain") or item.get("domain"), "content": content, "summary": item.get("summary") or item.get("snippet") or "", "language": item.get("language"), "published_at": item.get("published_at"), "fetched_at": datetime.now(timezone.utc).isoformat(), "last_verified_at": datetime.now(timezone.utc).isoformat(), "freshness_ttl_seconds": freshness_ttl_seconds, "authority_score": max(0.0, min(1.0, authority_score)), "verification_score": max(0.0, min(1.0, verification_score)), "confidence_score": max(0.0, min(1.0, authority_score * 0.45 + verification_score * 0.55)), "status": "active", "metadata": item.get("metadata") or {}}
    try:
        existing = supabase.table("web_documents").select("id").eq("company_id", company_id).eq("url_hash", payload["url_hash"]).limit(1).execute()
        if existing.data:
            doc_id = existing.data[0]["id"]
            supabase.table("web_documents").update(payload).eq("id", doc_id).execute()
        else:
            created = supabase.table("web_documents").insert(payload).execute()
            doc_id = created.data[0]["id"] if created.data else None
        if doc_id: _persist_claim_candidates(company_id, doc_id, content, verification_score, authority_score)
        return doc_id
    except Exception as error:
        print("[WEB MEMORY STORE WARNING]", error); return None

def build_context(memory: Dict[str, Any], max_chars: int = 9000) -> str:
    chunks: List[str] = []
    used = 0
    for row in memory.get("results", []):
        text = row.get("content") or row.get("summary") or ""
        if not text: continue
        block = f"SOURCE: {row.get('title') or row.get('source_domain') or row.get('canonical_url')}\nURL: {row.get('canonical_url')}\nCONTENT: {text}"
        if used + len(block) > max_chars: break
        chunks.append(block); used += len(block)
    return "\n\n".join(chunks)
