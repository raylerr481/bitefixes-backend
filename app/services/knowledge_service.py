"""BiteFixes Knowledge Service + evidence-ranked Internet research."""
from typing import Any, Dict

from app.database.supabase import database
from app.services.internet_problem_research_service import research_problem
from app.services.web_research_engine_v2 import research_problem_v2


def _problem_hypothesis(message: str, intent: str | None) -> Dict[str, Any]:
    problem = {
        "category": intent or "general_support",
        "intent": intent,
        "device": None,
        "platform": None,
        "symptoms": [],
        "state": "ANALYSIS",
    }
    text = (message or "").lower()
    if any(x in text for x in ("android", "redmi", "samsung", "xiaomi", "motorola", "galaxy", "celular", "telefono", "teléfono", "móvil", "movil")):
        problem["device"] = "smartphone"
        problem["platform"] = "android"
    if any(x in text for x in ("virus", "malware", "infectado", "infectada", "anuncios", "popups", "publicidad")):
        problem["category"] = "suspected_malware"
        problem["symptoms"] = ["possible malware or unwanted behavior"]
    return problem


def _internet_context(message: str, intent: str | None, language: str | None) -> Dict[str, Any]:
    problem = _problem_hypothesis(message, intent)
    try:
        return research_problem_v2(message=message, problem=problem, language=language or "es")
    except Exception as error:
        print("[WEB RESEARCH V2 ERROR]", error)
        return research_problem(message=message, problem=problem, language=language or "es")


def search_knowledge(message: str, company_id: int = None, intent: str = None, language: str = None):
    """Return local knowledge enriched with comparative public-web evidence."""
    if not message:
        return None
    best = None
    try:
        query = database.table("knowledge_base").select("*").eq("is_active", True)
        if company_id:
            query = query.eq("company_id", company_id)
        result = query.execute()
        items = result.data or []
        if intent:
            matches = [item for item in items if item.get("intent") == intent]
            if matches:
                items = matches
        if language:
            lang_matches = [item for item in items if item.get("language") == language]
            if lang_matches:
                items = lang_matches
        words = [w.strip(".,!?;:") for w in message.lower().split() if len(w) >= 3]
        score_best = 0
        for item in items:
            content = " ".join(str(item.get(k, "")) for k in ("title", "question", "answer", "keywords")).lower()
            score = sum(1 for word in words if word in content)
            if score > score_best:
                score_best, best = score, item
        if not best and items:
            best = items[0]
    except Exception as error:
        print("[KNOWLEDGE ERROR]", error)

    internet = _internet_context(message, intent, language)
    if best is None and not internet.get("best"):
        return None
    result = dict(best or {})
    result["internet_research"] = internet
    result["evidence_sources"] = internet.get("matches", [])
    result["research_confidence"] = internet.get("confidence", 0.0)
    result["research_method"] = internet.get("method", "evidence_ranked_multi_query_v2")
    result["research_contradictions"] = internet.get("contradictions", [])
    result["research_risk_buckets"] = internet.get("risk_buckets", {})
    return result


def find_knowledge(message, company_id=None, intent=None, language=None):
    return search_knowledge(message, company_id, intent, language)
