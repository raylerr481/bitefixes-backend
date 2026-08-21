"""Governed web intelligence with persistent Bitey web memory."""
from __future__ import annotations
import hashlib, json, os, re, time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse
from app.ai.bitey_search import search as bitey_search
from app.services.web_memory_service import build_context, record_search, search_memory, store_document
CURRENT_MARKERS={"today","latest","current","now","recent","price","prices","version","release","update","news","2026","2025","regulation","law","licence","license","availability","weather","stock"}
PROCEDURAL_MARKERS={"como","cómo","how","trocar","cambiar","reemplazar","reparar","arreglar","instalar","desmontar","montar","abrir","quitar","poner","pantalla","tela","screen","display","bateria","batería","conector","camara","cámara","teclado"}
_CACHE: Dict[str, tuple[float, Dict[str, Any]]]={}
@dataclass(frozen=True)
class WebPolicy:
    ttl_seconds:int=int(os.getenv("BITEY_WEB_CACHE_TTL","900")); max_queries:int=int(os.getenv("BITEY_WEB_MAX_QUERIES","3")); max_results:int=int(os.getenv("BITEY_WEB_MAX_RESULTS","8")); verification_min_score:float=float(os.getenv("BITEY_WEB_VERIFY_SCORE","0.72")); memory_ttl_seconds:int=int(os.getenv("BITEY_WEB_MEMORY_TTL","2592000")); memory_max_results:int=int(os.getenv("BITEY_WEB_MEMORY_MAX_RESULTS","5"))
POLICY=WebPolicy()
def needs_web(message:str,*,intent:Optional[str]=None,knowledge_found:bool=False)->bool:
    text=(message or "").lower(); words=set(re.findall(r"[a-z0-9À-ÿ-]+",text))
    if words & CURRENT_MARKERS:return True
    if knowledge_found and intent in {None,"support","conversation","general"} and len(words) <= 8:return False
    if words & PROCEDURAL_MARKERS and (words & {"como","cómo","how","trocar","cambiar","reemplazar","reparar","arreglar","instalar","desmontar","montar","pantalla","tela","screen","display"}):return True
    if not knowledge_found and len(words)>=10:return True
    return intent in {"research","comparison","troubleshooting","software_update","product_research"}
def build_queries(message:str,*,intent:Optional[str]=None,max_queries:int|None=None)->List[str]:
    text=re.sub(r"\s+"," ",(message or "").strip())
    if not text:return []
    limit=max_queries or POLICY.max_queries; queries=[text]
    if intent:queries.append(f"{intent} {text}")
    lowered=text.lower()
    if any(marker in lowered.split() for marker in ("latest","current","today","version","update")):queries.append(f"{text} official documentation")
    return list(dict.fromkeys(queries))[:limit]
def _domain(url:str)->str:return(urlparse(url).hostname or "").lower().removeprefix("www.")
def _domain_score(url:str)->float:
    host=_domain(url)
    if not host:return 0.0
    if host.endswith(".gov") or ".gov." in host:return 1.0
    if host.endswith(".edu") or ".edu." in host:return .95
    if host in {"microsoft.com","support.microsoft.com","learn.microsoft.com","apple.com","developer.apple.com","python.org","docs.python.org","supabase.com","render.com","github.com","wordpress.com"}:return .98
    if host.startswith("docs."):return .90
    return .55
def _tokenise(text:str)->set[str]:return{t for t in re.findall(r"[a-z0-9À-ÿ]{3,}",(text or "").lower()) if t not in {"the","and","for","with","from","this","that","para","com","uma","que"}}
def _normalise_result(item:Dict[str,Any],query:str)->Optional[Dict[str,Any]]:
    url=str(item.get("url") or item.get("link") or "").strip(); title=str(item.get("title") or "").strip(); snippet=str(item.get("snippet") or item.get("content") or item.get("description") or item.get("body") or "").strip()
    if not url or not title:return None
    relevance_tokens=len(_tokenise(query)&_tokenise(f"{title} {snippet}")); relevance=min(1.0,relevance_tokens/max(3,len(_tokenise(query))*.35)); authority=_domain_score(url)
    return {"url":url,"title":title,"snippet":snippet[:2500],"content":snippet[:12000],"domain":_domain(url),"authority_score":round(authority,3),"relevance_score":round(relevance,3),"score":round(.55*relevance+.45*authority,3),"retrieved_at":item.get("retrieved_at") or datetime.now(timezone.utc).isoformat()}
def _deduplicate(results:Iterable[Dict[str,Any]])->List[Dict[str,Any]]:
    seen=set();output=[]
    for item in results:
        key=hashlib.sha256((item["url"].rstrip("/")+"|"+item["title"].lower()).encode()).hexdigest()
        if key not in seen:seen.add(key);output.append(item)
    return output
def _cache_key(message:str,queries:List[str],intent:Optional[str])->str:return hashlib.sha256(json.dumps({"message":message.strip().lower(),"queries":queries,"intent":intent},sort_keys=True).encode()).hexdigest()
def _cache_get(key:str)->Optional[Dict[str,Any]]:
    entry=_CACHE.get(key)
    if not entry:return None
    expires,value=entry
    if expires<=time.time():_CACHE.pop(key,None);return None
    cached=dict(value);cached["cache_hit"]=True;return cached
def _cache_put(key:str,value:Dict[str,Any])->None:_CACHE[key]=(time.time()+POLICY.ttl_seconds,dict(value))
def _verify(results:List[Dict[str,Any]],query:str)->Dict[str,Any]:
    domains={item["domain"] for item in results if item.get("domain")};strong=[item for item in results if item.get("score",0)>=POLICY.verification_min_score];token_sets=[_tokenise(f"{item['title']} {item['snippet']}") for item in strong];corroborated=False
    if len(token_sets)>=2:
        common=token_sets[0].copy()
        for token_set in token_sets[1:]:common&=token_set
        corroborated=len(common)>=3
    return {"verified":bool(corroborated and len(domains)>=2 and len(strong)>=2),"corroborated":corroborated,"independent_domains":len(domains),"strong_sources":len(strong),"verification_score":round(min(1.0,len(strong)/3*.4+len(domains)/3*.3+(.3 if corroborated else 0)),3),"note":"corroboration is evidence, not a guarantee of factual correctness","query":query}
def _memory_response(memory:Dict[str,Any],message:str,company_id:int)->Dict[str,Any]:
    context=build_context(memory);results=[]
    for row in memory.get("results",[]):results.append({"url":row.get("canonical_url"),"title":row.get("title"),"snippet":row.get("summary") or row.get("content") or "","domain":row.get("source_domain"),"authority_score":row.get("authority_score",0),"verification_score":row.get("verification_score",0),"score":round(float(row.get("authority_score",0))*.45+float(row.get("verification_score",0))*.55,3),"from_memory":True,"fetched_at":row.get("fetched_at")})
    return {"used":True,"memory_hit":True,"memory_fresh":True,"external_used":False,"queries":[message],"results":results,"providers":["bitey_web_memory"],"grounding_status":"memory_grounded","verification":{"verified":True,"verification_score":max((r.get("verification_score",0) for r in results),default=0),"note":"reused previously verified web evidence"},"context":context,"cache_hit":False,"learning_candidate":False,"company_id":company_id}
def search_web(message:str,*,intent:Optional[str]=None,limit:int|None=None,company_id:Optional[int]=None)->Dict[str,Any]:
    queries=build_queries(message,intent=intent);max_results=limit or POLICY.max_results
    if company_id and not(set(re.findall(r"[a-z0-9À-ÿ-]+",message.lower()))&CURRENT_MARKERS):
        memory=search_memory(company_id,message,POLICY.memory_max_results)
        if memory.get("fresh"):
            record_search(company_id,message,"bitey_web_memory",local_hit_count=len(memory.get("results",[])),freshness_required=False);return _memory_response(memory,message,company_id)
    key=_cache_key(message,queries,intent);cached=_cache_get(key)
    if cached:return cached
    raw=[];errors=[];providers=[]
    for query in queries:
        try:
            result=bitey_search(query,max_results);raw.extend(result.get("results") or [])
            if result.get("provider") and result["provider"] not in providers:providers.append(result["provider"])
        except Exception as exc:errors.append(type(exc).__name__)
    results=[n for item in raw if(n:=_normalise_result(item,message))];results=sorted(_deduplicate(results),key=lambda item:item["score"],reverse=True)[:max_results];verification=_verify(results,message)
    if company_id and results:
        for item in results:store_document(company_id,item,verification_score=verification["verification_score"],authority_score=item["authority_score"],freshness_ttl_seconds=POLICY.memory_ttl_seconds)
    response={"used":bool(results),"memory_hit":False,"memory_fresh":False,"external_used":bool(results),"queries":queries,"results":results,"errors":errors,"providers":providers,"provider_configured":bool(providers),"grounding_status":"verified" if verification["verified"] else ("grounded" if results else "unavailable"),"verification":verification,"cache_hit":False,"learning_candidate":bool(verification["verified"] and results),"context":"\n\n".join(f"SOURCE: {r['title']}\nURL: {r['url']}\nCONTENT: {r['snippet']}" for r in results)}
    _cache_put(key,response)
    if company_id:record_search(company_id,message,providers[0] if providers else "unavailable",local_hit_count=0,external_used=bool(results),freshness_required=True)
    return response
