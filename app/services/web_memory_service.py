"""Bitey Web Memory: persistent, freshness-aware retrieval of researched web evidence."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.supabase_client import supabase


def _normalize_query(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _hash_url(url: str) -> str:
    return hashlib.sha256((url or "").strip().encode("utf-8")).hexdigest()


def _stale(row: Dict[str, Any]) -> bool:
    if row.get("is_stale") is not None:
        return bool(row["is_stale"])
    stamp = row.get("last_verified_at") or row.get("fetched_at")
    if not stamp:
        return True
    try:
        dt = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        ttl = int(row.get("freshness_ttl_seconds") or 2592000)
        return (datetime.now(timezone.utc) - dt).total_seconds() > ttl
    except Exception:
        return True


def search_memory(company_id: int, query: str, limit: int = 5) -> Dict[str, Any]:
    normalized = _normalize_query(query)
    if not normalized:
        return {"found": False, "fresh": False, "stale": False, "results": []}
    try:
        result = supabase.rpc(
            "search_bitey_web_memory",
            {"p_company_id": company_id, "p_query": normalized, "p_limit": max(1, min(limit, 20))},
        ).execute()
        rows = result.data or []
    except Exception as error:
        return {"found": False, "fresh": False, "stale": False, "results": [], "error": str(error)}

    stale_count = sum(1 for row in rows if _stale(row))
    fresh_rows = [row for row in rows if not _stale(row)]
    return {
        "found": bool(rows),
        "fresh": bool(fresh_rows),
        "stale": bool(rows) and not bool(fresh_rows),
        "stale_count": stale_count,
        "results": rows,
        "normalized_query": normalized,
    }


def record_search(company_id: int, query: str, source: str, *, customer_id: Optional[int] = None,
                  cache_hit: bool = False, local_hit_count: int = 0,
                  external_used: bool = False, freshness_required: bool = False,
                  metadata: Optional[Dict[str, Any]] = None) -> None:
    try:
        supabase.table("web_searches").insert({
            "company_id": company_id,
            "customer_id": customer_id,
            "query": query,
            "normalized_query": _normalize_query(query),
            "source": source,
            "cache_hit": cache_hit,
            "local_hit_count": local_hit_count,
            "external_used": external_used,
            "freshness_required": freshness_required,
            "metadata": metadata or {},
        }).execute()
    except Exception as error:
        print("[WEB MEMORY AUDIT WARNING]", error)


def store_document(company_id: Optional[int], item: Dict[str, Any], *, verification_score: float = 0.0,
                   authority_score: float = 0.5, freshness_ttl_seconds: int = 2592000) -> Optional[int]:
    url = str(item.get("url") or item.get("canonical_url") or "").strip()
    if not url:
        return None
    payload = {
        "company_id": company_id,
        "canonical_url": url,
        "url_hash": _hash_url(url),
        "title": item.get("title"),
        "source_domain": item.get("source_domain") or item.get("domain"),
        "content": item.get("content") or item.get("snippet") or "",
        "summary": item.get("summary") or item.get("snippet") or "",
        "language": item.get("language"),
        "published_at": item.get("published_at"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "last_verified_at": datetime.now(timezone.utc).isoformat(),
        "freshness_ttl_seconds": freshness_ttl_seconds,
        "authority_score": max(0.0, min(1.0, authority_score)),
        "verification_score": max(0.0, min(1.0, verification_score)),
        "status": "active",
        "metadata": item.get("metadata") or {},
    }
    try:
        existing = supabase.table("web_documents").select("id").eq("company_id", company_id).eq("url_hash", payload["url_hash"]).limit(1).execute()
        if existing.data:
            doc_id = existing.data[0]["id"]
            supabase.table("web_documents").update(payload).eq("id", doc_id).execute()
            return doc_id
        created = supabase.table("web_documents").insert(payload).execute()
        return created.data[0]["id"] if created.data else None
    except Exception as error:
        print("[WEB MEMORY STORE WARNING]", error)
        return None


def build_context(memory: Dict[str, Any], max_chars: int = 9000) -> str:
    chunks: List[str] = []
    used = 0
    for row in memory.get("results", []):
        text = row.get("content") or row.get("summary") or ""
        if not text:
            continue
        block = f"SOURCE: {row.get('title') or row.get('source_domain') or row.get('canonical_url')}\nURL: {row.get('canonical_url')}\nCONTENT: {text}"
        if used + len(block) > max_chars:
            break
        chunks.append(block)
        used += len(block)
    return "\n\n".join(chunks)
