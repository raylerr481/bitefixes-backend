"""BiteFixes Decision Engine V27 — governed orchestration and conversational guardrails."""
from difflib import SequenceMatcher
from typing import Any, Dict, Optional
from app.services.company_service import get_company_context
from app.services.business_reasoning_service import resolve_business_reasoning
from app.services.service_resolver import resolve_service
from app.services.workflows.workflow_service import execute_workflow
from app.services.sales_engine import generate_sales_response
from app.ai.trigger_engine import evaluate as evaluate_triggers

try:
    from app.services.ai_provider import ai_provider
    from app.ai.consultation_gate import evaluate as evaluate_ai_consultation
    from app.ai.ai_council import consult as consult_ai
    from app.ai.evaluator import evaluate_candidates
except Exception:
    ai_provider = evaluate_ai_consultation = consult_ai = evaluate_candidates = None

SALES_INTENTS={"ai_assistant","sales","quote","purchase"}
SUPPORT_INTENTS={"computer_repair","hardware_upgrade","windows_installation","mobile_repair","cctv_installation","camera_installation","network_configuration","software_problem","remote_support","cctv_repair","cctv_configuration","camera_replacement","wifi_configuration","router_configuration","vpn_configuration","network_diagnosis","server_support","microsoft365_support","cloud_support","data_recovery","virus_malware","performance_problem","screen_repair","battery_replacement","charging_port","camera_repair","software_mobile","data_transfer"}
QUOTE_INTENTS={"ai_assistant","sales","quote","purchase","cctv_installation","camera_installation","network_configuration","hardware_upgrade"}
GREETING_WORDS={"hola","hello","hi","hey","oi","ola","buenas","buenos dias","buenas tardes","buenas noches","bom dia","boa tarde","boa noite"}
MOBILE_CATEGORY_WORDS={"celular","celulares","movil","moviles","telefono","telefonos","telefone","telefones","phone","mobile","mobiles"}
FOLLOWUP_WORDS={"como","cómo","donde","dónde","ubicacion","ubicación","direccion","dirección","cuanto","cuánto","precio","costo","coste","horario","horarios","cuando","cuándo","reparar","repararlo","arreglar","arreglarlo","ayuda","pueden","puedo"}

def _reasoning_response(reasoning:Dict[str,Any], language:Optional[str])->Optional[str]:
    step=reasoning.get("next_step")
    if not step:return None
    if step.get("type")=="collect_requirements":
        names=[r.get("name") for r in step.get("requirements",[]) if r.get("name")]
        if not names:return None
        return {"pt-BR":"Para orientá-lo melhor, preciso de: ","en":"To guide you better, I need: ","es":"Para orientarte mejor, necesito: "}.get(language,"Para orientarte mejor, necesito: ")+", ".join(names)+"."
    if step.get("type")=="clarify_need":
        need=(step.get("needs") or [{}])[0]; return need.get("description") or need.get("name")
    if step.get("type")=="present_solution":
        solution=(step.get("solutions") or [{}])[0]; return solution.get("description") or solution.get("name")
    return None

def _is_greeting(message:str)->bool:
    value=" ".join(str(message or "").lower().strip().split())
    if value in GREETING_WORDS:return True
    return len(value) >= 4 and any(SequenceMatcher(None,value,g).ratio() >= 0.82 for g in {"hola","hello","ola"})

def _is_mobile_category(message:str)->bool:
    words=set(str(message or "").lower().strip().split()); return bool(words) and words.issubset(MOBILE_CATEGORY_WORDS)

def _is_contextual_followup(message:str, inherited:bool)->bool:
    if not inherited:return False
    words={w.strip(".,!?;:") for w in str(message or "").lower().strip().split()}
    return bool(words & FOLLOWUP_WORDS) or "?" in str(message)

def _knowledge_answer(knowledge:Any)->Optional[str]:
    if isinstance(knowledge,dict):
        answer=knowledge.get("answer") or knowledge.get("response") or knowledge.get("text")
        if answer:return str(answer).strip()
    return None

def _business_location(business_context:Optional[Dict[str,Any]])->Optional[str]:
    if not isinstance(business_context,dict):return None
    for source in (business_context.get("business_profile"),business_context.get("company")):
        if isinstance(source,dict):
            for key in ("address","full_address","location","address_line","street_address","city_address"):
                value=source.get(key)
                if value:return str(value).strip()
    return None

def _external_consultation(message:str,language:Optional[str],intent:Dict[str,Any],business_context:Optional[Dict[str,Any]],knowledge=None,memory=None)->Dict[str,Any]:
    if not all((evaluate_ai_consultation,consult_ai)):
        return {"ai_used":False,"reason":"ai_orchestration_unavailable"}
    trigger_plan=evaluate_triggers(message=message,intent=intent,knowledge=knowledge,memory=memory or {},language=language)
    if not trigger_plan.names:
        return {"ai_used":False,"reason":"no_trigger","triggers":[],"providers_requested":0}
    confidence=float(intent.get("confidence",0) or 0)
    complexity=min(1.0,max(0.0,len(message)/300))
    novelty=0.8 if "FRESH_INFORMATION" in trigger_plan.names else (0.8 if not intent.get("intent") else 0.3)
    gap=0.8 if "KNOWLEDGE_GAP" in trigger_plan.names else 0.2
    impact=0.7 if intent.get("intent") in {"ai_assistant","sales","quote"} else 0.2
    gate=evaluate_ai_consultation(confidence=confidence,complexity=complexity,novelty=novelty,knowledge_gap=gap,business_impact=impact,estimated_cost=0.0,trigger_names=trigger_plan.names)
    if not gate.consult:return {"ai_used":False,"reason":gate.reason,"triggers":list(trigger_plan.names),"capabilities":list(trigger_plan.capabilities),"gate_value":gate.estimated_value}
    max_providers=min(gate.max_providers,trigger_plan.max_providers)
    context={"intent":intent,"business_context":business_context or {},"triggers":list(trigger_plan.names),"capabilities":list(trigger_plan.capabilities),"memory":memory or {}}
    candidates=consult_ai(message,language=language or "es",context=context,max_providers=max_providers,capabilities=trigger_plan.capabilities)
    evaluation=evaluate_candidates(candidates,core_confidence=confidence) if evaluate_candidates else {"status":"not_evaluated"}
    return {"ai_used":bool(candidates),"gate_reason":gate.reason,"gate_value":gate.estimated_value,"triggers":list(trigger_plan.names),"capabilities":list(trigger_plan.capabilities),"providers_requested":max_providers,"providers_used":[c.get("provider") for c in candidates],"candidates":candidates,"evaluation":evaluation,"learning_candidate":bool(evaluation.get("learning_candidate"))}

def make_decision(company_id:int,customer:Dict,message:str,intent:Dict,knowledge=None,memory=None,language=None,channel="unknown",business_context:Optional[Dict[str,Any]]=None):
    intent=intent or {}
    if _is_greeting(message):
        greeting={"pt-BR":"Olá! Sou Bitey. Como posso ajudá-lo?","en":"Hello! I'm Bitey. How can I help?"}.get(language,"Hola, soy Bitey. ¿Cómo puedo ayudarte?")
        return {"action":"conversation","create_ticket":False,"requires_quote":False,"ticket_type":None,"response":greeting,"workflow":None,"service":None,"service_id":None,"reasoning":{},"metadata":{"reason":"greeting","intent_suppressed":bool(intent.get("intent")),"confidence":float(intent.get("confidence",0) or 0)}}
    if business_context is None:
        try: business_context=get_company_context(company_id)
        except Exception as error: print("[BUSINESS CONTEXT WARNING]",error); business_context=None
    memory=memory if isinstance(memory,dict) else {}
    active_intent=memory.get("last_intent")
    inherited=bool(intent.get("context_inherited"))
    if active_intent and _is_contextual_followup(message,True) and (inherited or float(intent.get("confidence",0) or 0)<0.70):
        intent=dict(intent); intent["intent"]=active_intent; intent["context_inherited"]=True; intent["context_source"]="active_conversation"; intent["confidence"]=max(0.70,float(memory.get("last_confidence",0) or 0))
    ai_metadata=_external_consultation(message,language,intent,business_context,knowledge,memory)
    intent_name=intent.get("intent"); confidence=float(intent.get("confidence",0) or 0); inherited=bool(intent.get("context_inherited"))
    if intent_name and _is_contextual_followup(message,inherited):
        answer=_knowledge_answer(knowledge); location=_business_location(business_context); lowered=str(message or "").lower()
        asks_location=any(term in lowered for term in ("donde","dónde","ubicacion","ubicación","direccion","dirección","residen"))
        if asks_location and location and location not in (answer or ""):
            location_text={"pt-BR":f"Nossa localização: {location}.","en":f"Our location: {location}.","es":f"Nuestra ubicación: {location}."}.get(language,f"Nuestra ubicación: {location}."); answer=(answer+"\n\n"+location_text) if answer else location_text
        if answer:
            service=resolve_service(company_id,intent_name,business_context=business_context)
            return {"action":"conversation","create_ticket":False,"requires_quote":False,"ticket_type":None,"response":answer,"workflow":None,"service":service,"service_id":service.get("id") if service else None,"reasoning":{},"metadata":{"reason":"contextual_followup","context_inherited":True,"context_source":"active_conversation","intent":intent_name,"confidence":confidence,**ai_metadata}}
        if intent_name=="mobile_repair":
            response={"pt-BR":"Posso orientar sobre o reparo do celular. Diga se o problema é tela, bateria, carregamento ou outro.","en":"I can guide you about the phone repair. Tell me whether the problem is the screen, battery, charging or something else.","es":"Puedo orientarte sobre la reparación del celular. Dime si el problema es la pantalla, batería, carga u otro."}.get(language,"Puedo orientarte sobre la reparación del celular. Dime qué problema presenta el equipo.")
            service=resolve_service(company_id,intent_name,business_context=business_context)
            return {"action":"conversation","create_ticket":False,"requires_quote":False,"ticket_type":None,"response":response,"workflow":None,"service":service,"service_id":service.get("id") if service else None,"reasoning":{},"metadata":{"reason":"contextual_followup_no_knowledge","context_inherited":True,"intent":intent_name,"confidence":confidence,**ai_metadata}}
    reasoning=resolve_business_reasoning(company_id,intent_name) if intent_name else {}
    service=resolve_service(company_id,intent_name,business_context=business_context) if intent_name else None
    service_id=service.get("id") if service else None
    requires_quote=intent_name in QUOTE_INTENTS
    metadata={"intent":intent_name,"confidence":confidence,"requires_quote":requires_quote,"business_context_loaded":bool(business_context),"ai_scope_loaded":bool(business_context and business_context.get("ai_scope")),"business_reasoning_found":reasoning.get("reasoning_found",False),**ai_metadata}
    semantic_response=_reasoning_response(reasoning,language)
    if intent_name in SALES_INTENTS:
        return {"action":"sales","create_ticket":True,"requires_quote":requires_quote,"ticket_type":"sales","response":semantic_response or generate_sales_response(intent_name,customer.get("full_name","Cliente"),memory),"service":service,"service_id":service_id,"workflow":None,"reasoning":reasoning,"metadata":metadata}
    if intent_name in SUPPORT_INTENTS:
        if intent_name=="mobile_repair" and _is_mobile_category(message):
            response={"pt-BR":"Claro. Posso ajudar com celulares. Diga o que está acontecendo com o aparelho e, se puder, informe marca, modelo e desde quando ocorre o problema.","en":"Sure. I can help with mobile phones. Tell me what is happening and, if possible, include the brand, model and when it started.","es":"Claro. Puedo ayudarte con celulares. Dime qué le está pasando al equipo y, si puedes, indícame la marca, el modelo y desde cuándo ocurre."}.get(language,"Claro. Puedo ayudarte con celulares. Dime qué le está pasando al equipo.")
            return {"action":"conversation","create_ticket":False,"requires_quote":False,"ticket_type":None,"response":response,"workflow":intent_name,"workflow_result":{"success":False,"reason":"diagnostic_details_required"},"ticket":None,"service":service,"service_id":service_id,"reasoning":reasoning,"metadata":metadata}
        workflow_result=execute_workflow(intent=intent_name,company_id=company_id,customer_id=customer.get("id"),service_id=service_id,message=message,knowledge=knowledge,language=language,business_context=business_context,intent_data=intent)
        ok=bool(workflow_result.get("success")); response=semantic_response or workflow_result.get("response") or "Voy a ayudarte con el diagnóstico."
        return {"action":"workflow","create_ticket":ok,"requires_quote":requires_quote if ok else False,"ticket_type":"technical_support" if ok else None,"response":response,"workflow":intent_name,"workflow_result":workflow_result,"ticket":workflow_result.get("ticket"),"service":service,"service_id":service_id,"reasoning":reasoning,"metadata":metadata}
    if not intent_name:
        clarification={"pt-BR":"Posso ajudá-lo com suporte técnico, celulares, computadores, redes, câmeras ou IA para empresas. O que você precisa?","en":"I can help with technical support, phones, computers, networks, cameras, or business AI. What do you need?"}.get(language,"Puedo ayudarte con soporte técnico, celulares, computadoras, redes, cámaras o IA para empresas. ¿Qué necesitas?")
        return {"action":"conversation","create_ticket":False,"requires_quote":False,"ticket_type":None,"response":clarification,"workflow":None,"service":None,"service_id":None,"reasoning":{},"metadata":{"reason":"intent_not_detected",**ai_metadata}}
    return {"action":"conversation","create_ticket":False,"requires_quote":False,"ticket_type":None,"response":semantic_response or "Puedo ayudarte a identificar lo que necesitas. ¿Qué problema o servicio buscas?","workflow":None,"service":service,"service_id":service_id,"reasoning":reasoning,"metadata":metadata}

def decision_engine(company_id,customer,message,intent,knowledge=None,memory=None,language=None,business_context=None):
    return make_decision(company_id,customer,message,intent,knowledge,memory,language,business_context=business_context)
