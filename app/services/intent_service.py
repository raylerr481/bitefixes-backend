"""BiteFixes - Bitey Intent Engine V11.

Deterministic intent detection with typo tolerance and durable conversation
recovery. The engine must be able to understand short, misspelled follow-ups
without requiring the user to repeat the service name.
"""

import re
import unicodedata
from difflib import SequenceMatcher

from app.database.supabase import database
from app.services.concept_engine import understand as understand_concept, propose_learning, record_learning


def normalize(text):
    if not text:
        return ""
    text = str(text).lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


INTENT_RULES = {
    "ai_assistant": ["asistente ia", "assistente ia", "chatbot", "bot whatsapp", "automatizar empresa", "automatizar whatsapp", "inteligencia artificial"],
    "cctv_installation": ["camera", "cameras", "camara", "camaras", "camera seguranca", "cameras seguranca", "cctv", "monitoramento", "instalar camera", "instalar cameras", "security camera", "camara seguridad", "camara de seguridad"],
    "computer_repair": ["no prende", "no enciende", "nao liga", "nao funciona", "pantalla negra", "tela preta", "reparar computador", "reparar computadora", "arreglar pc", "reparar pc", "arreglar computadora", "virus", "computadora", "computadoras", "ordenador", "ordenadores", "pc", "notebook", "portatil", "laptop"],
    "hardware_upgrade": ["ssd", "ram", "memoria", "upgrade", "lento", "melhorar", "mejorar", "actualizar memoria", "aumentar memoria", "mas ram"],
    "network_configuration": ["configurar wifi", "configurar minha rede", "configurar rede", "configuracao wifi", "configuracao de rede", "configurar roteador", "configurar router", "configurar internet", "instalar wifi", "instalar rede", "rede wifi", "wifi", "roteador", "router"],
    "remote_support": ["suporte remoto", "soporte remoto", "remote support", "atendimento remoto", "ayuda remota"],
    "mobile_repair": [
        "celular", "celulares", "movil", "moviles", "telefono", "telefonos", "telefone", "telefones", "phone", "mobile", "mobiles",
        "reparar celular", "arreglar celular", "consertar celular", "reparar telefone", "consertar telefone", "mobile repair",
        "celular quebrado", "celular roto", "celular roro", "movil roto", "movil roro", "telefono roto", "telefono roro",
        "pantalla rota", "pantalla del telefono", "pantalla de telefono", "pantalla de celular", "pantalla rota celular",
        "tela quebrada", "tela do celular", "tela do telefone", "display quebrado", "display roto", "display do celular", "vidro quebrado", "vidrio roto",
    ],
    "windows_installation": ["instalar windows", "instalacion windows", "instalacao windows", "formatar computador", "formatar notebook", "formatear pc"],
}

GREETING_VARIANTS = ("hola", "hello", "hi", "hey", "oi", "ola", "buenas", "buenos dias", "buenas tardes", "buenas noches")
PHONE_WORDS = {"telefono", "telefonos", "celular", "celulares", "movil", "moviles", "telefone", "telefones", "phone", "mobile", "mobiles", "telfono", "telfono"}
REPAIR_WORDS = {"reparar", "repararlo", "repararmi", "repararme", "reparo", "reparacion", "reparacion", "arreglar", "arreglarlo", "arreglo", "consertar", "conserto", "roto", "rota", "roto", "quebrado", "quebrada"}
DIAGNOSTIC_WORDS = {"diagnostico", "diagnosticar", "diagnosis", "problema", "fallo", "fallando", "revisar", "revision", "revisalo", "revisarlo"}


def fuzzy(token, vocabulary, threshold=0.72):
    token = normalize(token)
    if len(token) < 4:
        return False
    return any(SequenceMatcher(None, token, candidate).ratio() >= threshold for candidate in vocabulary)


def is_greeting(message):
    text = normalize(message)
    if text in GREETING_VARIANTS:
        return True
    if len(text.split()) <= 3:
        return any(SequenceMatcher(None, text, greeting).ratio() >= 0.72 for greeting in GREETING_VARIANTS)
    return False


def mobile_semantic_signal(text):
    words = normalize(text).split()
    has_phone = any(w in PHONE_WORDS or fuzzy(w, PHONE_WORDS) for w in words)
    has_repair = any(w in REPAIR_WORDS or fuzzy(w, REPAIR_WORDS) for w in words)
    has_diagnostic = any(w in DIAGNOSTIC_WORDS or fuzzy(w, DIAGNOSTIC_WORDS) for w in words)
    return has_phone and (has_repair or has_diagnostic)


def recover_active_ticket(context):
    """Recover the active service from the database when conversation memory is incomplete."""
    if not isinstance(context, dict):
        return None
    customer_id = context.get("customer_id")
    company_id = context.get("company_id")
    if not customer_id:
        return None
    try:
        query = database.table("tickets").select("id,intent,service_id,status,created_at").eq("customer_id", customer_id).in_("status", ["open", "in_progress", "pending"]).order("created_at", desc=True).limit(1)
        if company_id is not None:
            query = query.eq("company_id", company_id)
        result = query.execute()
        if result.data:
            return result.data[0]
    except Exception as error:
        print("[ACTIVE TICKET RECOVERY WARNING]", error)
    return None


def get_synonyms():
    try:
        result = database.table("sinonimos_ia").select("*").execute()
        return result.data or []
    except Exception as error:
        print("[SYNONYMS ERROR]", error)
        return []


def get_company_services(company_id):
    if not company_id:
        return []
    try:
        result = database.table("services").select("id,name,description,intent,capability_id,is_active").eq("company_id", company_id).eq("is_active", True).execute()
        return result.data or []
    except Exception as error:
        print("[SERVICE INTENT ERROR]", error)
        return []


def keyword_match(keyword, text):
    keyword_words = normalize(keyword).split()
    text_words = set(normalize(text).split())
    return bool(keyword_words) and all(word in text_words for word in keyword_words)


def phrase_score(phrase, text):
    phrase = normalize(phrase)
    if not phrase:
        return 0
    if keyword_match(phrase, text):
        return 18 + min(len(phrase.split()), 4) * 2
    # Correct small spelling errors in meaningful phrases without making the
    # matcher dangerously broad.
    phrase_words = phrase.split()
    text_words = normalize(text).split()
    if len(phrase_words) == 1 and len(phrase) >= 5:
        best = max((SequenceMatcher(None, phrase, token).ratio() for token in text_words), default=0)
        return 12 if best >= 0.84 else 0
    if len(phrase_words) > 1 and len(text_words) >= len(phrase_words):
        matches = 0
        for p in phrase_words:
            if any(SequenceMatcher(None, p, t).ratio() >= 0.84 for t in text_words):
                matches += 1
        if matches == len(phrase_words):
            return 14 + len(phrase_words) * 2
    return 0


def score_company_services(text, company_id, scores):
    for service in get_company_services(company_id):
        service_intent = service.get("intent")
        if not service_intent:
            continue
        score = phrase_score(service.get("name", ""), text) + phrase_score(service.get("description", ""), text) + phrase_score(service_intent.replace("_", " "), text)
        if score:
            scores[service_intent] = scores.get(service_intent, 0) + score


def _normalize_confidence(raw_score, scores):
    if not scores:
        return 0.0
    top = float(raw_score or 0)
    total = float(sum(max(0, value) for value in scores.values()))
    if total <= 0:
        return 0.0
    dominance = top / total
    absolute = min(1.0, top / 80.0)
    return round(min(0.99, 0.55 * dominance + 0.45 * absolute), 4)


def detect_intent(message, company_id=None, context=None):
    try:
        text = normalize(message)
        scores = {}
        concept = understand_concept(message, context=context)
        primary_concept = concept.get("concept") or {}

        # Greetings are deliberately neutral; decision_engine owns the response.
        if is_greeting(message):
            return {"intent": None, "confidence": 0.0, "raw_score": 0, "scores": {}, "concept": concept, "learning": {"status": "not_applicable"}, "greeting": True}

        for item in get_synonyms():
            keyword = item.get("keyword", "")
            intent = item.get("intent")
            weight = item.get("weight", 1) or 1
            if intent and keyword_match(keyword, text):
                scores[intent] = scores.get(intent, 0) + weight * 10

        for intent, words in INTENT_RULES.items():
            for word in words:
                match_score = phrase_score(word, text)
                if match_score:
                    scores[intent] = scores.get(intent, 0) + match_score

        for signal in primary_concept.get("diagnostic_signals", []):
            scores[signal] = scores.get(signal, 0) + max(12, int(float(primary_concept.get("confidence", 0.7)) * 25))

        if mobile_semantic_signal(text):
            scores["mobile_repair"] = scores.get("mobile_repair", 0) + 35

        score_company_services(text, company_id, scores)

        last = (context or {}).get("last_intent")
        if last:
            if last == "mobile_repair" and (mobile_semantic_signal(text) or any(w in text.split() for w in {"celular", "telefono", "movil", "pantalla", "display", "tela", "diagnostico", "reparar", "repararlo", "ubicacion", "donde", "como"})):
                scores[last] = scores.get(last, 0) + 50
            elif last in scores:
                scores[last] += 10

        # Durable fallback: if conversation memory was not written/read, the
        # active ticket is still authoritative context for the customer.
        active_ticket = recover_active_ticket(context)
        if active_ticket and active_ticket.get("intent"):
            active_intent = active_ticket["intent"]
            if not scores:
                return {"intent": active_intent, "confidence": 0.88, "raw_score": 70, "scores": {active_intent: 70}, "concept": concept, "learning": {"status": "context_recovered"}, "context_recovered": True, "active_ticket": active_ticket}
            scores[active_intent] = scores.get(active_intent, 0) + 35

        if not scores:
            learning = propose_learning(message, intent=None, language=(context or {}).get("language", "auto"))
            record_learning(learning, company_id=(context or {}).get("company_id"), conversation_id=(context or {}).get("conversation_id"))
            return {"intent": None, "confidence": 0.0, "raw_score": 0, "scores": {}, "concept": concept, "learning": learning}

        intent = max(scores, key=scores.get)
        raw_score = scores[intent]
        confidence = _normalize_confidence(raw_score, scores)
        learning = propose_learning(message, intent=intent, language=(context or {}).get("language", "auto"))
        record_learning(learning, company_id=(context or {}).get("company_id"), conversation_id=(context or {}).get("conversation_id"))
        print("[INTENT SCORES]", scores, "confidence=", confidence, "concept=", primary_concept.get("concept"))
        return {"intent": intent, "confidence": confidence, "raw_score": raw_score, "scores": scores, "concept": concept, "learning": learning, "active_ticket": active_ticket}
    except Exception as error:
        print("[INTENT ERROR]", error)
        return {"intent": None, "confidence": 0.0, "raw_score": 0, "scores": {}, "concept": {"known": False, "knowledge_gap": True}, "learning": {"status": "error", "validated": False}}
