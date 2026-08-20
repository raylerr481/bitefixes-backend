"""Single governed entry point for external AI and web consultation."""
from typing import Any, Dict

from app.ai.consultation_gate import evaluate
from app.ai.ai_council import consult
from app.ai.evaluator_suggestions import evaluate_suggestions
from app.ai.learning_candidates import record_candidate
from app.ai.web_intelligence import needs_web, search_web
from app.ai.web_learning import record_web_candidate

try:
    from app.cognitive.cognitive_engine import cognitive_observe
except ImportError:
    cognitive_observe = None


PROCEDURAL_MARKERS = {
    "como", "cómo", "how", "trocar", "troca", "cambiar", "cambiarla", "cambiarlo",
    "reemplazar", "reparar", "arreglar", "instalar", "desmontar", "montar",
    "abrir", "quitar", "poner", "cambiar", "pantalla", "tela", "screen",
    "display", "bateria", "batería", "conector", "camara", "cámara", "teclado",
}


def _is_procedural_request(message: str) -> bool:
    text = (message or "").strip().lower()
    if not text:
        return False
    words = set(text.replace("?", " ").replace("¿", " ").split())
    has_how = bool(words & {"como", "cómo", "how"})
    has_action = bool(words & {"trocar", "troca", "cambiar", "reemplazar", "reparar", "arreglar", "instalar", "desmontar", "montar", "abrir", "quitar", "poner"})
    has_component = bool(words & {"pantalla", "tela", "screen", "display", "bateria", "batería", "conector", "camara", "cámara", "teclado"})
    return (has_how and has_action) or (has_action and has_component)


def consult_if_valuable(
    *,
    company_id: int,
    message: str,
    language: str,
    intent: Dict[str, Any],
    context: Dict[str, Any],
    conversation_id: Any = None,
) -> Dict[str, Any]:
    confidence = float(intent.get("confidence", 0) or 0)
    intent_name = intent.get("intent")
    knowledge_found = not bool(context.get("knowledge_gap", 0))
    procedural = _is_procedural_request(message)

    cognitive = {"status": "unavailable"}
    if cognitive_observe:
        try:
            cognitive = cognitive_observe(
                customer_id=int(context.get("customer_id") or 0),
                conversation_id=str(conversation_id or "unknown"),
                message=message,
                intent=intent_name,
                service_id=context.get("last_service") or context.get("service_id"),
                confidence=confidence,
            )
        except Exception as error:
            print("[COGNITIVE WARNING]", error)
            cognitive = {"status": "error", "error": str(error)}

    web = {"used": False, "grounding_status": "not_needed", "results": [], "queries": []}
    if needs_web(message, intent=intent_name, knowledge_found=knowledge_found):
        web = search_web(message, intent=intent_name, company_id=company_id)
        if web.get("learning_candidate"):
            record_web_candidate(company_id=company_id, message=message, web=web, conversation_id=conversation_id)

    gate = evaluate(
        confidence=confidence,
        complexity=float(context.get("complexity", 0) or 0),
        novelty=float(context.get("novelty", 0) or 0),
        knowledge_gap=float(context.get("knowledge_gap", 0) or 0),
        business_impact=float(context.get("business_impact", 0) or 0),
        estimated_cost=float(context.get("estimated_cost", 0) or 0),
        force_advisory=procedural,
        advisory_reason="procedural_how_to" if procedural else "",
    )

    if not gate.consult and web.get("used"):
        return {"used": False, "reason": gate.reason, "gate": gate.__dict__, "suggestions": [], "web_grounding": web, "cognitive": cognitive, "process": ["core_analysis", "cognitive_observation", "web_grounding"]}
    if not gate.consult:
        return {"used": False, "reason": gate.reason, "gate": gate.__dict__, "web_grounding": web, "cognitive": cognitive, "process": ["core_analysis", "cognitive_observation"]}

    enriched_context = {**context, "web_grounding": web, "cognitive_state": cognitive}
    suggestions = consult(message, language=language, context=enriched_context, max_providers=gate.max_providers)
    evaluation = evaluate_suggestions(suggestions, core_confidence=confidence)

    if evaluation.get("learning_candidate") and evaluation.get("selected"):
        selected = evaluation["selected"]
        record_candidate(company_id=company_id, message=message, provider=selected.get("provider", "unknown"), suggestion=selected, evaluation=evaluation, conversation_id=conversation_id)

    return {
        "used": bool(suggestions),
        "reason": gate.reason,
        "gate": gate.__dict__,
        "suggestions": suggestions,
        "evaluation": evaluation,
        "web_grounding": web,
        "cognitive": cognitive,
        "process": ["core_analysis", "cognitive_observation"] + (["web_grounding"] if web.get("used") else []) + ["external_ai_consultation", "comparative_evaluation", "learning_candidate"],
    }
