"""Bitey multi-model consultation, research and coherence gate."""
from __future__ import annotations
import re
from typing import Any, Dict
from app.ai.ai_council import consult
from app.ai.contextual_message_resolver import resolve_contextual_message
from app.ai.learning_candidates import record_candidate
from app.ai.web_intelligence import needs_web, search_web
from app.ai.web_learning import record_web_candidate


# High-confidence geographic entities used only to detect explicit answer/query conflicts.
# This is a contradiction guard, not a location resolver or a general knowledge database.
_PLACE_ALIASES = {
    "españa": ("españa", "espana", "spain"),
    "spain": ("españa", "espana", "spain"),
    "filipinas": ("filipinas", "philippines"),
    "philippines": ("filipinas", "philippines"),
    "brasil": ("brasil", "brazil"),
    "brazil": ("brasil", "brazil"),
    "portugal": ("portugal",),
    "cuba": ("cuba",),
    "méxico": ("méxico", "mexico"),
    "mexico": ("méxico", "mexico"),
    "argentina": ("argentina",),
    "chile": ("chile",),
    "colombia": ("colombia",),
    "perú": ("perú", "peru"),
    "peru": ("perú", "peru"),
    "estados unidos": ("estados unidos", "united states", "usa", "u.s."),
    "united states": ("estados unidos", "united states", "usa", "u.s."),
    "esteio": ("esteio",),
    "porto alegre": ("porto alegre",),
    "madrid": ("madrid",),
    "canarias": ("canarias", "canary islands"),
}

def _explicit_place_conflict(answer: str, message: str) -> str | None:
    """Detect a foreign-country claim in an answer to a single-country question."""
    question = str(message or "").casefold()
    response = str(answer or "").casefold()
    country_keys = {
        "españa", "spain", "filipinas", "philippines", "brasil", "brazil",
        "portugal", "cuba", "méxico", "mexico", "argentina", "chile",
        "colombia", "perú", "peru", "estados unidos", "united states",
    }
    requested_countries = {
        canonical for canonical, aliases in _PLACE_ALIASES.items()
        if canonical in country_keys
        and any(re.search(r"(?<!\\w)" + re.escape(alias) + r"(?!\\w)", question) for alias in aliases)
    }
    if not requested_countries:
        return None
    # Explicit comparisons legitimately mention more than one country.
    comparison = any(term in question for term in (
        "compara", "comparar", "diferencia entre", "versus", " vs ", "compare", "between",
    ))
    if comparison:
        return None
    for canonical, aliases in _PLACE_ALIASES.items():
        if canonical not in country_keys or canonical in requested_countries:
            continue
        if any(re.search(r"(?<!\\w)" + re.escape(alias) + r"(?!\\w)", response) for alias in aliases):
            return f"answer_mentions_unrequested_place:{canonical}"
    return None

def _general_answer_quality(answer: str, message: str) -> tuple[float, list[str]]:
    """Apply narrow, high-confidence checks to general questions without token-overlap scoring."""
    score = 1.0
    reasons: list[str] = []
    if not str(answer or "").strip():
        return 0.0, ["empty_answer"]
    conflict = _explicit_place_conflict(answer, message)
    if conflict:
        score -= 0.85
        reasons.append(conflict)
    return max(0.0, min(1.0, score)), reasons


def _contextual_inputs(context: Dict[str, Any]) -> tuple[list[dict[str, Any]], str | None, str | None, str | None]:
    memory = context.get("memory") or {}; conversation = context.get("conversation") or {}
    state = context.get("contextual_state") or memory.get("problem_state") or {}; profile = context.get("company_ai_profile") or {}
    recent = conversation.get("recent_turns") or memory.get("recent_turns") or context.get("history") or []
    entity = (state.get("active_problem") or conversation.get("active_problem") or memory.get("active_problem") or state.get("active_object") or state.get("active_category") or conversation.get("active_object") or conversation.get("active_category") or memory.get("active_object") or memory.get("active_topic") or profile.get("company_name"))
    goal = context.get("active_goal") or memory.get("active_goal") or state.get("active_goal") or state.get("customer_goal")
    active_url = memory.get("active_url") or state.get("active_url")
    return recent, entity, goal, active_url


def _research_query(message: str, context: Dict[str, Any], intent_name: str | None) -> str:
    state = context.get("contextual_state") or (context.get("memory") or {}).get("problem_state") or {}
    recent, entity, goal, active_url = _contextual_inputs(context)
    candidates = [state.get("active_problem"), state.get("active_category"), state.get("active_object"), state.get("active_model"), state.get("active_service"), (context.get("conversation") or {}).get("active_problem"), (context.get("conversation") or {}).get("active_category"), (context.get("conversation") or {}).get("active_object"), (context.get("conversation") or {}).get("active_model"), (context.get("memory") or {}).get("last_service")]
    anchors=[]
    for value in candidates:
        if isinstance(value,dict): value=value.get("name") or value.get("title") or value.get("slug") or value.get("problem")
        value=str(value or "").strip()
        if value and value not in anchors: anchors.append(value)
    if intent_name and intent_name not in anchors: anchors.append(intent_name)
    base=" ".join(str(message or "").strip().split())
    if not base: return ""
    resolved=resolve_contextual_message(base,history=recent,active_entity=entity,active_goal=goal); base=resolved.get("resolved_message") or base
    if active_url and len(base.split())<=8 and active_url not in base: base=f"{base} [context_url: {active_url}]"
    return base if len(base.split())>=8 else (" ".join(anchors[:3]+[base]) if anchors else base)


def _coherence_score(answer: str, message: str, context: Dict[str, Any]) -> tuple[float,list[str]]:
    state=context.get("contextual_state") or (context.get("memory") or {}).get("problem_state") or {}
    active_problem=str(state.get("active_problem") or (context.get("memory") or {}).get("active_problem") or "").strip().lower()
    active_goal=str(state.get("active_goal") or context.get("active_goal") or (context.get("memory") or {}).get("active_goal") or state.get("customer_goal") or "").strip().lower()
    category=str(state.get("active_category") or "").strip().lower(); active_object=str(state.get("active_object") or "").strip().lower(); active_model=str(state.get("active_model") or "").strip().lower()
    entity_only=bool(state.get("entity_only")); reasons=[]; score=1.0; answer_l=answer.lower()
    topic_terms={"security":("virus","malware","seguridad","infect","anuncio","aplicación","app"),"performance":("lento","rendimiento","memoria","cpu","optim","velocidad"),"startup":("enciende","inicia","arranca","arranque","pantalla negra","boot"),"connectivity":("wifi","internet","red","conexión","conexion","bluetooth","señal"),"power":("batería","bateria","carga","energía","energia","apaga","calienta"),"display":("pantalla","display","touch","brillo"),"audio":("audio","sonido","micrófono","microfono","altavoz"),"camera":("cámara","camara","cctv","dvr","nvr","video"),"printing":("impresora","imprime","printer","tinta","toner"),"accounts":("cuenta","contraseña","acceso","login","autentic"),"data":("datos","archivo","recuper","backup","copia"),"physical_damage":("roto","dañado","agua","golpe","pantalla"),"business_ai":("crm","saas","automat","ia","marketing","proceso")}
    request_goal=any(x in active_goal for x in ("request_service","solicitud","instalar","crear","configurar","comprar","contratar","montar","hacer","adquirir","implementar")) or str(state.get("state") or "").upper()=="GOAL_REQUEST"
    restart_markers=("qué problema","que problema","what problem","what issue","síntoma","sintoma","qué falla","que falla","avería","averia")
    if request_goal and not active_problem and any(term in answer_l for term in restart_markers):
        score-=0.80; reasons.append("answer_restarts_diagnostic_for_active_request")
    if entity_only and active_problem:
        allowed=topic_terms.get(category,())
        if allowed and not any(term in answer_l for term in allowed): score-=0.55; reasons.append("answer_does_not_preserve_active_problem")
        if any(term in answer_l for term in restart_markers): score-=0.30; reasons.append("answer_restarts_problem_discovery")
        if active_model and active_model not in answer_l and active_object and active_object not in answer_l: score-=0.05; reasons.append("answer_drops_new_device_context")
    # Once a startup/power problem is established, asking again for device, OS, or the basic problem is a hard continuity violation.
    if category == "startup" or re.search(r"\b(no enciende|no prende|no arranca|no inicia)\b", active_problem):
        repeated_fields=("qué tipo de equipo","que tipo de equipo","tipo de equipo","qué dispositivo","que dispositivo","qué sistema operativo","que sistema operativo","qué sistema","que sistema","cuál es el problema","cual es el problema","describe el problema","qué ocurre","que ocurre")
        if any(term in answer_l for term in repeated_fields):
            score-=0.75; reasons.append("answer_repeats_known_diagnostic_fields")
        if any(term in answer_l for term in ("contacto","número de teléfono","numero de telefono","horario","agendar","agenda", "cita")) and not any(term in answer_l for term in ("diagnóstico","diagnostico","fuente","cable","tomacorriente","enchufe","energía","energia")):
            score-=0.50; reasons.append("answer_requests_service_contact_before_diagnosis")
    if category=="security" and re.search(r"\b(conectividad|wifi|wi-fi|internet|datos móviles)\b",answer_l) and not re.search(r"\b(seguridad|virus|malware|anuncio|aplicación|app)\b",answer_l): score-=0.65; reasons.append("security_problem_reclassified_as_connectivity")
    # Also validate the actual question, not only the previously active technical issue.
    # Keep this guard narrow: lexical similarity alone rejects many correct paraphrases.
    general_score, general_reasons = _general_answer_quality(answer, message)
    score = min(score, general_score)
    reasons.extend(general_reasons)
    return max(0.0,min(1.0,score)),reasons


def _select_coherent(results:list[dict[str,Any]],message:str,context:Dict[str,Any]):
    evaluated=[]
    for item in results:
        answer=str(item.get("answer") or "").strip(); score,reasons=_coherence_score(answer,message,context); enriched=dict(item); enriched["coherence"]={"score":round(score,3),"reasons":reasons,"passed":score>=0.60}; evaluated.append(enriched)
    passed=[x for x in evaluated if x.get("coherence",{}).get("passed")]; return (max(passed,key=lambda x:x.get("coherence",{}).get("score",0.0)) if passed else None),evaluated


def consult_if_valuable(*,company_id:int,message:str,language:str,intent:Dict[str,Any],context:Dict[str,Any],conversation_id:Any=None)->Dict[str,Any]:
    intent_name=intent.get("intent"); knowledge_found=not bool(context.get("knowledge_gap",0)); recent,entity,goal,active_url=_contextual_inputs(context)
    contextual=resolve_contextual_message(message,history=recent,active_entity=entity,active_goal=goal)
    web={"used":False,"grounding_status":"not_needed","results":[],"queries":[],"research_candidate":bool(contextual.get("research_candidate"))}; research_query=_research_query(message,context,intent_name)
    should_research=contextual.get("research_candidate") or needs_web(message,intent=intent_name,knowledge_found=knowledge_found)
    if should_research:
        web=search_web(research_query or message,intent=intent_name,company_id=company_id); web["research_candidate"]=bool(contextual.get("research_candidate"))
        if web.get("learning_candidate"): record_web_candidate(company_id=company_id,message=message,web=web,conversation_id=conversation_id)
    state=context.get("contextual_state") or (context.get("memory") or {}).get("problem_state") or {}
    enriched_context={**context,"knowledge":{"company_knowledge":context.get("knowledge"),"web_grounding":web},"web_grounding":web,"research_query":research_query,"contextual_resolution":contextual,"contextual_state":state,"cognitive_authority":"external_ai_council","bitey_role":"enterprise_context_memory_and_governance","continuity_guard":{"active_goal":state.get("active_goal") or context.get("active_goal"),"active_problem":state.get("active_problem"),"active_category":state.get("active_category"),"active_object":state.get("active_object"),"active_model":state.get("active_model"),"rule":"The current goal remains authoritative unless evidence establishes a new goal/problem."}}
    effective_message=contextual.get("resolved_message") or message; max_providers=max(1,min(int(context.get("max_ai_providers") or 2),3)); results=consult(effective_message,language=language,context=enriched_context,max_providers=max_providers)
    if not results: return {"used":False,"reason":"no_external_ai_response","suggestions":[],"web_grounding":web,"research_query":research_query,"authority":"external_ai_council"}
    selected,evaluated=_select_coherent(results,message,enriched_context)
    if selected is None: return {"used":False,"reason":"coherence_gate_failed","suggestions":evaluated,"web_grounding":web,"research_query":research_query,"authority":"external_ai_council","coherence_gate":{"passed":False,"rule":"reject answers that lose the active goal/problem, repeat known diagnostic fields, request contact before diagnosis, or introduce an unrelated diagnostic domain"}}
    answer=str(selected.get("answer") or "").strip(); provider=str(selected.get("provider") or "unknown")
    if answer: record_candidate(company_id=company_id,message=message,provider=provider,suggestion=selected,evaluation={"authority":"external_ai_council","mode":"coherence_gated_multi_model","coherence":selected.get("coherence"),"candidate_count":len(evaluated),"bitey_is_apprentice":True},conversation_id=conversation_id)
    return {"used":True,"reason":"external_ai_council_selected","answer":answer,"provider":provider,"suggestions":evaluated,"selection":{"authority":"external_ai_council","mode":"highest_coherence_passed","provider":provider},"coherence_gate":selected.get("coherence"),"web_grounding":web,"research_query":research_query,"contextual_resolution":contextual,"process":["channel_input","enterprise_context","problem_state","contextual_resolution","web_research","multi_model_consultation","coherence_evaluation","coherence_gate","response","learning_evidence_storage","channel_output"]}
