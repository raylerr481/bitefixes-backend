"""External-AI consultation service.

External providers are the cognitive authority. Bitey may prepare context,
request governed web evidence, persist telemetry and learn operationally, but it
does not score, rank, rewrite or veto an external-AI response.
"""
from typing import Any, Dict

from app.ai.consultation_gate import evaluate
from app.ai.ai_council import consult
from app.ai.learning_candidates import record_candidate
from app.ai.web_intelligence import needs_web, search_web
from app.ai.web_learning import record_web_candidate
from app.ai.evaluation_store import record_provider_evaluation

try:
    from app.cognitive.cognitive_engine import cognitive_observe
except ImportError:
    cognitive_observe = None

GREETING_WORDS = {"hola", "hello", "hi", "hey", "oi", "ola", "buenas", "buenos dias", "buenas tardes", "buenas noches"}


def _is_greeting(message: str) -> bool:
    text = " ".join((message or "").strip().lower().split())
    return text in GREETING_WORDS


def _is_substantive_request(message: str) -> bool:
    return bool((message or "").strip()) and not _is_greeting(message)


def consult_if_valuable(*, company_id: int, message: str, language: str, intent: Dict[str, Any], context: Dict[str, Any], conversation_id: Any = None) -> Dict[str, Any]:
    confidence = float(intent.get("confidence", 0) or 0)
    intent_name = intent.get("intent")
    knowledge_found = not bool(context.get("knowledge_gap", 0))
    substantive = _is_substantive_request(message)

    cognitive = {"status": "unavailable"}
    if cognitive_observe:
        try:
            cognitive = cognitive_observe(customer_id=int(context.get("customer_id") or 0), conversation_id=str(conversation_id or "unknown"), message=message, intent=intent_name, service_id=context.get("last_service") or context.get("service_id"), confidence=confidence)
        except Exception as error:
            print("[COGNITIVE WARNING]", type(error).__name__); cognitive = {"status": "error"}

    web = {"used": False, "grounding_status": "not_needed", "results": [], "queries": []}
    if needs_web(message, intent=intent_name, knowledge_found=knowledge_found):
        web = search_web(message, intent=intent_name, company_id=company_id)
        if web.get("learning_candidate"):
            record_web_candidate(company_id=company_id, message=message, web=web, conversation_id=conversation_id)

    # This gate only controls infrastructure/resource policy. It does not
    # evaluate or judge an external-AI answer. Substantive user requests are
    # always advisory so the external rector gets the first cognitive turn.
    gate = evaluate(confidence=confidence, complexity=float(context.get("complexity", 0) or 0), novelty=float(context.get("novelty", 0) or 0), knowledge_gap=float(context.get("knowledge_gap", 0) or 0), business_impact=float(context.get("business_impact", 0) or 0), estimated_cost=float(context.get("estimated_cost", 0) or 0), force_advisory=substantive or _is_greeting(message), advisory_reason="external_rector_primary")
    if not gate.consult:
        return {"used": False, "reason": gate.reason, "gate": gate.__dict__, "suggestions": [], "web_grounding": web, "cognitive": cognitive}

    enriched_context = {**context, "web_grounding": web, "cognitive_state": cognitive}
    suggestions = consult(message, language=language, context=enriched_context, max_providers=1)
    interaction_id = str(conversation_id or context.get("conversation_id") or "unknown")

    if not suggestions:
        return {"used": False, "reason": "no_external_ai_response", "gate": gate.__dict__, "suggestions": [], "web_grounding": web, "cognitive": cognitive}

    # First healthy external rector owns the response. No Bitey scoring or
    # comparative selection is performed after the provider answers.
    selected = suggestions[0]
    answer = str(selected.get("answer") or "").strip()
    if answer:
        record_provider_evaluation(company_id=company_id, interaction_id=interaction_id, provider=str(selected.get("provider") or "unknown"), task_type=str(intent_name or "general_reasoning"), answer=answer, context={**enriched_context, "verified_evidence": bool(selected.get("search_verified")), "cognitive_state": selected.get("contextual_state") or cognitive, "evaluation_authority": "external_ai"})
        record_candidate(company_id=company_id, message=message, provider=str(selected.get("provider") or "unknown"), suggestion=selected, evaluation={"authority": "external_ai", "mode": "self_evaluated"}, conversation_id=conversation_id)

    return {"used": bool(answer), "reason": gate.reason, "gate": gate.__dict__, "answer": answer, "provider": selected.get("provider"), "suggestions": suggestions, "selection": {"authority": "external_ai", "mode": "first_healthy_provider", "provider": selected.get("provider")}, "web_grounding": web, "cognitive": cognitive, "process": ["context_preparation", "external_ai_consultation", "provider_health", "provider_telemetry", "external_ai_self_evaluation", "learning_candidate"]}
