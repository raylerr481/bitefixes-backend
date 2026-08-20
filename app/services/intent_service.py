"""Bitey Intent Engine V12 — hybrid LLM + deterministic understanding."""
import re
import unicodedata
from difflib import SequenceMatcher
from app.database.supabase import database
from app.services.concept_engine import understand as understand_concept, propose_learning, record_learning

try:
    from app.ai.llm_gateway import understand as llm_understand
except Exception:
    llm_understand = None


def normalize(text):
    if not text: return ""
    text = unicodedata.normalize("NFD", str(text).lower().strip())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9\s]", " ", text).split())

INTENT_RULES = {
    "ai_assistant":["asistente ia","assistente ia","chatbot","bot whatsapp","automatizar empresa","automatizar whatsapp","inteligencia artificial"],
    "cctv_installation":["camera","cameras","camara","camaras","camera seguranca","cameras seguranca","cctv","monitoramento","instalar camera","instalar cameras","security camera","camara seguridad"],
    "computer_repair":["no prende","no enciende","nao liga","nao funciona","pantalla negra","tela preta","reparar computador","reparar computadora","arreglar pc","reparar pc","virus","computadora","ordenador","pc","notebook","portatil","laptop"],
    "hardware_upgrade":["ssd","ram","memoria","upgrade","lento","melhorar","mejorar","actualizar memoria","aumentar memoria","mas ram"],
    "network_configuration":["configurar wifi","configurar minha rede","configurar rede","configuracao wifi","configuracao de rede","configurar roteador","configurar router","configurar internet","instalar wifi","instalar rede","rede wifi","wifi","roteador","router"],
    "remote_support":["suporte remoto","soporte remoto","remote support","atendimento remoto","ayuda remota"],
    "mobile_repair":["celular","celulares","movil","moviles","telefono","telefonos","telefone","telefones","phone","mobile","mobiles","reparar celular","arreglar celular","consertar celular","reparar telefone","consertar telefone","mobile repair","celular roto","movil roto","telefono roto","pantalla rota","pantalla del telefono","pantalla de telefono","pantalla de celular","tela quebrada","tela do celular","display quebrado","display roto","vidro quebrado","vidrio roto"],
    "windows_installation":["instalar windows","instalacion windows","instalacao windows","formatar computador","formatar notebook","formatear pc"],
}
GREETING_VARIANTS=("hola","hello","hi","hey","oi","ola","buenas","buenos dias","buenas tardes","buenas noches","bom dia","boa tarde","boa noite")
PHONE_WORDS={"telefono","telefonos","celular","celulares","movil","moviles","telefone","telefones","phone","mobile","mobiles","telfono","telfono","telf"}
REPAIR_WORDS={"reparar","repararlo","repararmi","repararme","reparo","reparacion","arreglar","arreglarlo","arreglo","consertar","conserto","roto","rota","quebrado","quebrada","arreglarmi"}
DIAGNOSTIC_WORDS={"diagnostico","diagnosticar","diagnosis","problema","fallo","fallando","revisar","revision","revisalo","revisarlo","diagnosktico","diagnostico"}

def fuzzy(token,vocabulary,threshold=0.70):
    token=normalize(token)
    if len(token)<3:return False
    return any(SequenceMatcher(None,token,c).ratio()>=threshold for c in vocabulary)

def is_greeting(message):
    text=normalize(message)
    if text in GREETING_VARIANTS:return True
    if len(text.split())<=3:return any(SequenceMatcher(None,text,g).ratio()>=0.68 for g in GREETING_VARIANTS)
    return False

def mobile_semantic_signal(text):
    words=normalize(text).split()
    has_phone=any(w in PHONE_WORDS or fuzzy(w,PHONE_WORDS) for w in words)
    has_repair=any(w in REPAIR_WORDS or fuzzy(w,REPAIR_WORDS) for w in words)
    has_diagnostic=any(w in DIAGNOSTIC_WORDS or fuzzy(w,DIAGNOSTIC_WORDS) for w in words)
    return has_phone and (has_repair or has_diagnostic)

def recover_active_ticket(context):
    if not isinstance(context,dict):return None
    customer_id=context.get("customer_id"); company_id=context.get("company_id")
    if not customer_id:return None
    try:
        query=database.table("tickets").select("id,intent,service_id,status,created_at").eq("customer_id",customer_id).in_("status",["open","in_progress","pending"]).order("created_at",desc=True).limit(1)
        if company_id is not None: query=query.eq("company_id",company_id)
        result=query.execute()
        return result.data[0] if result.data else None
    except Exception as error:
        print("[ACTIVE TICKET RECOVERY WARNING]",error); return None

def get_synonyms():
    try:return database.table("sinonimos_ia").select("*").execute().data or []
    except Exception as error: print("[SYNONYMS ERROR]",error); return []

def get_company_services(company_id):
    if not company_id:return []
    try:return database.table("services").select("id,name,description,intent,capability_id,is_active").eq("company_id",company_id).eq("is_active",True).execute().data or []
    except Exception as error: print("[SERVICE INTENT ERROR]",error); return []

def keyword_match(keyword,text):
    return bool(normalize(keyword).split()) and all(w in set(normalize(text).split()) for w in normalize(keyword).split())

def phrase_score(phrase,text):
    phrase=normalize(phrase)
    if not phrase:return 0
    if keyword_match(phrase,text):return 18+min(len(phrase.split()),4)*2
    pw=phrase.split(); tw=normalize(text).split()
    if len(pw)==1 and len(phrase)>=4:
        return 12 if max((SequenceMatcher(None,phrase,t).ratio() for t in tw),default=0)>=0.80 else 0
    if len(pw)>1 and len(tw)>=len(pw):
        matches=sum(1 for p in pw if any(SequenceMatcher(None,p,t).ratio()>=0.80 for t in tw))
        return 14+len(pw)*2 if matches==len(pw) else 0
    return 0

def score_company_services(text,company_id,scores):
    for service in get_company_services(company_id):
        si=service.get("intent")
        if not si:continue
        score=phrase_score(service.get("name", ""),text)+phrase_score(service.get("description", ""),text)+phrase_score(si.replace("_"," "),text)
        if score:scores[si]=scores.get(si,0)+score

def _normalize_confidence(raw,scores):
    if not scores:return 0.0
    total=float(sum(max(0,v) for v in scores.values())); top=float(raw or 0)
    if total<=0:return 0.0
    return round(min(0.99,0.55*(top/total)+0.45*min(1,top/80)),4)

def detect_intent(message,company_id=None,context=None):
    try:
        text=normalize(message); context=context or {}; scores={}
        concept=understand_concept(message,context=context); primary=concept.get("concept") or {}
        if is_greeting(message):return {"intent":None,"confidence":0.0,"raw_score":0,"scores":{},"concept":concept,"learning":{"status":"not_applicable"},"greeting":True}

        # LLM is the semantic layer. It may classify, but never executes actions.
        llm_result={}
        if llm_understand:
            llm_result=llm_understand(message=message,language=context.get("language","es"),context=context)
            llm_intent=llm_result.get("intent")
            if llm_intent and llm_intent not in {"unknown","none"}:
                llm_conf=float(llm_result.get("confidence",0) or 0)
                scores[llm_intent]=scores.get(llm_intent,0)+max(30,int(llm_conf*80))

        for item in get_synonyms():
            keyword=item.get("keyword",""); intent=item.get("intent"); weight=item.get("weight",1) or 1
            if intent and keyword_match(keyword,text):scores[intent]=scores.get(intent,0)+weight*10
        for intent,words in INTENT_RULES.items():
            for word in words:
                s=phrase_score(word,text)
                if s:scores[intent]=scores.get(intent,0)+s
        for signal in primary.get("diagnostic_signals",[]):scores[signal]=scores.get(signal,0)+max(12,int(float(primary.get("confidence",0.7))*25))
        if mobile_semantic_signal(text):scores["mobile_repair"]=scores.get("mobile_repair",0)+35
        score_company_services(text,company_id,scores)

        last=context.get("last_intent")
        if last:
            if last=="mobile_repair" and (mobile_semantic_signal(text) or any(w in text.split() for w in {"celular","telefono","movil","pantalla","display","tela","diagnostico","reparar","repararlo","ubicacion","donde","como"})):
                scores[last]=scores.get(last,0)+50
            elif last in scores:scores[last]+=10

        active_ticket=recover_active_ticket(context)
        if active_ticket and active_ticket.get("intent"):
            ai=active_ticket["intent"]
            if not scores:return {"intent":ai,"confidence":0.88,"raw_score":70,"scores":{ai:70},"concept":concept,"learning":{"status":"context_recovered"},"context_recovered":True,"active_ticket":active_ticket}
            scores[ai]=scores.get(ai,0)+35

        if not scores:
            learning=propose_learning(message,intent=None,language=context.get("language","auto")); record_learning(learning,company_id=context.get("company_id"),conversation_id=context.get("conversation_id"))
            return {"intent":None,"confidence":0.0,"raw_score":0,"scores":{},"concept":concept,"learning":learning,"llm":llm_result}
        intent=max(scores,key=scores.get); raw=scores[intent]; confidence=_normalize_confidence(raw,scores)
        learning=propose_learning(message,intent=intent,language=context.get("language","auto")); record_learning(learning,company_id=context.get("company_id"),conversation_id=context.get("conversation_id"))
        return {"intent":intent,"confidence":confidence,"raw_score":raw,"scores":scores,"concept":concept,"learning":learning,"active_ticket":active_ticket,"llm":llm_result,"entities":llm_result.get("entities",{}),"user_goal":llm_result.get("user_goal")}
    except Exception as error:
        print("[INTENT ERROR]",error)
        return {"intent":None,"confidence":0.0,"raw_score":0,"scores":{},"concept":{"known":False,"knowledge_gap":True},"learning":{"status":"error","validated":False}}
