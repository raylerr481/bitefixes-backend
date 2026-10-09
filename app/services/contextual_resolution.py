"""Generic semantic conversational interpretation for Bitey."""
from __future__ import annotations
import re
from typing import Any

_REQUEST_PATTERNS = (
    r"\bquiero\s+(?:instalar|crear|configurar|comprar|contratar|montar|hacer|adquirir|poner|implementar|desarrollar)\b",
    r"\b(?:deseo|necesito|busco|me gustaría|me gustaria)\s+(?:instalar|crear|configurar|comprar|contratar|montar|hacer|adquirir|poner|implementar|desarrollar)\b",
    r"\b(?:quiero|deseo|necesito|busco)\s+(?:una|un|el|la|las|los)\s+.+",
)
_SYMPTOM_MARKERS = ("no funciona","no enciende","no inicia","no arranca","está lento","esta lento","se congela","se bloquea","no muestra","no conecta","se desconecta","no carga","no graba","roto","rota","dañado","danado","error","problema","falla","falló","fallo")
_REFERENCE_MARKERS = ("allí","alli","allá","alla","ahí","ahi","eso","esa","ese","esto","esta","este","también","tambien","lo mismo","el mismo","la misma")
_TEMPORAL = {"mañana":"tomorrow","manana":"tomorrow","hoy":"today","ahora":"current","actualmente":"current","ayer":"yesterday","después":"after","despues":"after","luego":"after"}
_CORRECTIONS = ("no, me refiero","no me refiero","me refería","me referia","quise decir","quería decir","queria decir","no era eso","no es eso","no, hablo de","no hablo de","hablo de","me refiero a")
_INTENTS = {
 "weather": (r"\bqué tiempo hace\b",r"\bque tiempo hace\b",r"\bqué tiempo está haciendo\b",r"\bque tiempo esta haciendo\b",r"\bclima\b",r"\btemperatura\b",r"\bpronóstico\b",r"\bpronostico\b",r"\bllueve\b",r"\bllover\b"),
 "time": (r"\bqué hora\b",r"\bque hora\b",r"\bcuál es la hora\b",r"\bcual es la hora\b",r"\bhora actual\b",r"\bqué hora es\b",r"\bque hora es\b"),
 "price": (r"\bcuánto cuesta\b",r"\bcuanto cuesta\b",r"\bprecio\b",r"\bcosto\b",r"\bcotización\b",r"\bcotizacion\b",r"\bpresupuesto\b"),
 "how_to": (r"\bcómo puedo\b",r"\bcomo puedo\b",r"\bcómo se hace\b",r"\bcomo se hace\b",r"\bcómo hago\b",r"\bcomo hago\b"),
 "explanation": (r"\bqué es\b",r"\bque es\b",r"\bqué significa\b",r"\bque significa\b",r"\bpor qué\b",r"\bpor que\b",r"\bexplica\b",r"\bexplícame\b",r"\bexplicame\b"),
 "comparison": (r"\bcuál es mejor\b",r"\bcual es mejor\b",r"\bcompar",r"\bdiferencia entre\b"),
 "research": (r"\binvestiga\b",r"\bbusca información\b",r"\bbusca informacion\b",r"\banaliza\b",r"\bqué sabes sobre\b",r"\bque sabes sobre\b"),
 "purchase": (r"\bquiero comprar\b",r"\bnecesito comprar\b",r"\bqué compro\b",r"\bque compro\b",r"\brecomienda\b"),
 "support": (r"\bno funciona\b",r"\btengo un problema\b",r"\bno puedo\b",r"\berror\b",r"\bfalla\b",r"\bse rompió\b",r"\bse rompio\b",r"\bnecesito ayuda\b"),
}
_CAPABILITY = {"weather":"weather","time":"time","price":"pricing_or_quote","how_to":"instruction","explanation":"knowledge","comparison":"comparison","research":"research","purchase":"product_recommendation","support":"support_reasoning"}
_ACTION = {"weather":"get_weather","time":"get_time","price":"answer_or_quote","how_to":"explain_steps","explanation":"explain","comparison":"compare","research":"research","purchase":"recommend","support":"diagnose_or_assist"}

def _has_request_intent(text: str) -> bool:
    value=text.lower().strip()
    return any(re.search(p,value,re.I) for p in _REQUEST_PATTERNS)

def _has_symptom(text: str) -> bool:
    value=text.lower().strip()
    return any(x in value for x in _SYMPTOM_MARKERS)

def _history_has_request(history):
    return any(
        str(r.get("sender_type") or "").lower() in {"customer","user"}
        and (lambda t: t and _has_request_intent(t) and not _has_symptom(t))(str(r.get("message_content") or "").strip())
        for r in history
    )

def _text(row):
    return str(row.get("message_content") or row.get("content") or "").strip()

def _user_history(history):
    return [_text(r) for r in history if str(r.get("sender_type") or r.get("role") or "").lower() in {"customer","user"} and _text(r)]

def _location(texts):
    for t in reversed(texts):
        m=list(re.finditer(r"\b(?:en|desde|hacia|para)\s+([A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜ0-9 .,'-]{2,80})",t))
        if m: return re.sub(r"\s+"," ",m[-1].group(1).strip(" .,_-"))
        m=re.search(r"\b(?:España|Espana|Brasil|Portugal|México|Mexico|Argentina|Chile|Uruguay|Canarias|Madrid|Barcelona|Valencia|Sevilla|Lisboa|Porto Alegre|Esteio)\b",t,re.I)
        if m: return m.group(0)
    return None

def _anchors(state, history):
    prev=state.get("interpretation") if isinstance(state.get("interpretation"),dict) else {}
    a={k:prev.get(k) for k in ("topic","intent","location","object","model","goal","problem","subject") if prev.get(k) not in (None,"",[],{})}
    for k,v in {"location":state.get("active_location"),"object":state.get("active_object"),"model":state.get("active_model"),"goal":state.get("active_goal") or state.get("customer_goal"),"problem":state.get("active_problem"),"topic":state.get("active_category") or state.get("active_topic")}.items():
        if v not in (None,"",[],{}): a[k]=v
    loc=_location(_user_history(history))
    if loc: a["location"]=loc
    return a

def _classify(text, anchors, follow):
    lower=text.lower(); scores=[]
    for name,patterns in _INTENTS.items():
        n=sum(1 for p in patterns if re.search(p,lower,re.I))
        if n: scores.append((name,n))
    if scores:
        scores.sort(key=lambda x:(-x[1],x[0])); name,n=scores[0]
        return name,min(.98,.72+.08*min(n,3)),[x[0] for x in scores]
    if follow and anchors.get("intent"): return str(anchors["intent"]),.78,[str(anchors["intent"])]
    return None,0.0,[]

def interpret_context(state: dict[str,Any], current_message: str, history: list[dict[str,Any]]) -> dict[str,Any]:
    text=str(current_message or "").strip(); lower=text.lower(); follow=bool(history); anchors=_anchors(state,history)
    refs={}; ambiguity=[]; correction=any(x in lower for x in _CORRECTIONS)
    if any(re.search(r"\b"+re.escape(x)+r"\b",lower) for x in _REFERENCE_MARKERS):
        if anchors.get("location"): refs["location"]=anchors["location"]
        elif re.search(r"\b(all[ií]|all[aá]|ah[ií])\b",lower): ambiguity.append("location_reference")
        for k in ("topic","object","model","goal","problem","subject"):
            if anchors.get(k): refs[k]=anchors[k]
        refs["continuation"]=True
    for word,value in _TEMPORAL.items():
        if re.search(r"\b"+re.escape(word)+r"\b",lower):
            refs["time_reference"]=value
            if anchors.get("intent"): refs["intent"]=anchors["intent"]
            if anchors.get("location"): refs["location"]=anchors["location"]
            break
    # A correction is a semantic reset for intent inheritance: never let the old intent win merely because this is a short follow-up.
    intent,confidence,candidates=_classify(text,anchors,follow and not correction)
    if correction and intent is None:
        if re.search(r"\bhora\b",lower): intent,confidence="time",.84
        elif re.search(r"\b(clima|temperatura|tiempo|llueve)\b",lower): intent,confidence="weather",.84
        else: ambiguity.append("corrected_intent")
        refs["correction"]=True
        if anchors.get("intent"): refs["previous_intent_replaced"]=anchors["intent"]
    if re.search(r"\btiempo\b",lower) and not re.search(r"\bqué tiempo hace\b|\bque tiempo hace\b",lower):
        if not re.search(r"\b(hora|clima|temperatura|llueve|pronóstico|pronostico)\b",lower):
            if anchors.get("intent") in {"weather","time"}: intent,confidence=anchors["intent"],max(confidence,.78)
            else: ambiguity.append("time_or_weather")
    if len(text.split())<=8 and intent is None and anchors.get("intent") and not correction:
        intent,confidence=anchors["intent"],max(confidence,.78)
    entities={}
    for k in ("location","object","model","goal","problem"):
        v=refs.get(k) or anchors.get(k)
        if v not in (None,"",[],{}): entities[k]=v
    if "time_reference" in refs: entities["time_reference"]=refs["time_reference"]
    if intent: required=_CAPABILITY.get(intent,"conversation"); action=_ACTION.get(intent,"respond")
    else: required="clarification" if ambiguity else "conversation"; action="ask_clarification" if ambiguity else "respond"
    if refs: confidence=max(confidence,min(.92,.60+.1*len(refs)))
    if ambiguity: confidence=min(confidence or .55,.55)
    return {"message":text,"is_follow_up":follow,"correction":correction,"intent":intent,"intent_candidates":candidates,"topic":intent or anchors.get("topic"),"entities":entities,"reference_resolution":refs,"confidence":round(confidence,3),"ambiguity":sorted(set(ambiguity)),"interpretable":bool(intent and not ambiguity),"required_capability":required,"action":action,"anchors_used":anchors}

def resolve_context(state: dict[str,Any], current_message: str, history: list[dict[str,Any]]) -> dict[str,Any]:
    text=str(current_message or "").strip(); result=dict(state)
    result["interpretation"]=interpret_context(result,text,history)
    interpretation=result.get("interpretation") if isinstance(result.get("interpretation"),dict) else {}
    current_request=_has_request_intent(text); current_symptom=_has_symptom(text); prior_request=_history_has_request(history)
    # Explicitly corrected intent supersedes stale entities/problems from the previous topic.
    if interpretation.get("correction") and interpretation.get("intent"):
        new_intent=str(interpretation["intent"])
        previous_intent=str((state.get("interpretation") or {}).get("intent") or "")
        if previous_intent and previous_intent != new_intent:
            result["previous_intent"] = previous_intent
        result["active_intent"] = new_intent
        result["active_category"] = new_intent
        result["interpretation"]["previous_intent_replaced"] = previous_intent or None
        if new_intent not in {"support"}:
            result["active_problem"] = None
            result["hypotheses"] = []
            result["confirmed_facts"] = [f for f in result.get("confirmed_facts",[]) if f.get("type") not in {"problem","symptom"}]
        result["is_follow_up"] = bool(history)
    elif interpretation.get("correction") and not interpretation.get("intent"):
        # Do not silently continue the old topic after an ambiguous correction; ask what the user meant.
        result["active_intent"] = None
        result["interpretation"]["intent"] = None
        result["interpretation"]["topic"] = None
        result["interpretation"]["action"] = "ask_clarification"
        result["interpretation"]["required_capability"] = "clarification"
        result["interpretation"]["interpretable"] = False
        result["interpretation"]["ambiguity"] = sorted(set(result["interpretation"].get("ambiguity",[]) + ["corrected_intent"]))
    if not interpretation.get("correction") and current_request and not current_symptom:
        result.update({"active_problem":None,"active_category":None,"state":"GOAL_REQUEST","is_follow_up":bool(history)})
        result["customer_goal"]=result.get("customer_goal") or "REQUEST_SERVICE"; result["active_goal"]=result.get("active_goal") or result["customer_goal"]; result["hypotheses"]=[]
        result["confidence"]=max(float(result.get("confidence") or 0),.80)
        result["confirmed_facts"]=[f for f in result.get("confirmed_facts",[]) if f.get("type")!="problem"]
    elif not interpretation.get("correction") and prior_request and not current_symptom:
        result.update({"active_problem":None,"active_category":None,"state":"ENTITY_UPDATE" if result.get("entity_only") else "CONTINUATION","is_follow_up":True})
        result["customer_goal"]=result.get("customer_goal") or "REQUEST_SERVICE"; result["active_goal"]=result.get("active_goal") or result["customer_goal"]; result["hypotheses"]=[]
        result["confidence"]=max(float(result.get("confidence") or 0),.80)
        result["confirmed_facts"]=[f for f in result.get("confirmed_facts",[]) if f.get("type")!="problem"]
    return result
