"""BiteFixes - Bitey Intent Engine V10.
Multilingual + Context Aware + Company Service Aware + Concept Aware.

The intent matcher remains deterministic, while the Concept Engine adds a
semantic layer that can recognize variants and propose safe learning events.
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
    "ai_assistant": [
        "asistente ia", "assistente ia", "chatbot", "bot whatsapp",
        "automatizar empresa", "automatizar whatsapp", "inteligencia artificial",
    ],
    "cctv_installation": [
        "camera", "cameras", "camara", "camaras", "camera seguranca", "cameras seguranca",
        "cctv", "monitoramento", "instalar camera", "instalar cameras",
        "security camera", "camara seguridad", "camara de seguridad",
    ],
    "computer_repair": [
        "no prende", "no enciende", "nao liga", "nao funciona",
        "pantalla negra", "tela preta", "reparar computador", "reparar computadora",
        "arreglar pc", "reparar pc", "arreglar computadora", "virus",
        "computadora", "computadoras", "ordenador", "ordenadores", "pc", "notebook", "portatil", "laptop",
    ],
    "hardware_upgrade": [
        "ssd", "ram", "memoria", "upgrade", "lento", "melhorar", "mejorar",
        "actualizar memoria", "aumentar memoria", "mas ram",
    ],
    "network_configuration": [
        "configurar wifi", "configurar minha rede", "configurar rede",
        "configuracao wifi", "configuracao de rede", "configurar roteador",
        "configurar router", "configurar internet", "instalar wifi",
        "instalar rede", "rede wifi", "wifi", "roteador", "router",
    ],
    "remote_support": [
        "suporte remoto", "soporte remoto", "remote support",
        "atendimento remoto", "ayuda remota",
    ],
    "mobile_repair": [
        "celular", "celulares", "movil", "moviles", "telefono", "telefonos", "telefone", "telefones", "phone", "mobile", "mobiles",
        "reparar celular", "arreglar celular", "consertar celular",
        "reparar telefone", "consertar telefone", "mobile repair",
        "celular quebrado", "celular roto", "celular roro", "movil roto", "movil roro",
        "telefono roto", "telefono roro", "pantalla rota", "pantalla del telefono",
        "pantalla de telefono", "pantalla de celular", "pantalla rota celular",
        "tela quebrada", "tela do celular", "tela do telefone", "display quebrado",
        "display roto", "display do celular", "vidro quebrado", "vidrio roto",
    ],
    "windows_installation": [
        "instalar windows", "instalacion windows", "instalacao windows",
        "formatar computador", "formatar notebook", "formatear pc",
    ],
}


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
        result = (
            database.table("services")
            .select("id,name,description,intent,capability_id,is_active")
            .eq("company_id", company_id)
            .eq("is_active", True)
            .execute()
        )
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
    return 0


def fuzzy_token(token, candidates, threshold=0.82):
    token = normalize(token)
    if len(token) < 4:
        return False
    return any(SequenceMatcher(None, token, candidate).ratio() >= threshold for candidate in candidates)


def mobile_typo_signal(text):
    words = normalize(text).split()
    phone_words = {"telefono", "telefonos", "celular", "celulares", "movil", "moviles", "telefone", "telefones", "phone", "mobile"}
    screen_words = {"pantalla", "tela", "display", "screen", "apantalla"}
    broken_words = {"rota", "roto", "roro", "quebrada", "quebrado", "rompida", "rompido", "broken"}
    has_phone = any(word in phone_words or fuzzy_token(word, phone_words) for word in words)
    has_screen = any(word in screen_words or fuzzy_token(word, screen_words) for word in words)
    has_broken = any(word in broken_words or fuzzy_token(word, broken_words) for word in words)
    return (has_phone and has_broken) or (has_phone and has_screen)


def score_company_services(text, company_id, scores):
    for service in get_company_services(company_id):
        service_intent = service.get("intent")
        if not service_intent:
            continue
        score = 0
        score += phrase_score(service.get("name", ""), text)
        score += phrase_score(service.get("description", ""), text)
        score += phrase_score(service_intent.replace("_", " "), text)
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

        # Conceptual signals supplement, rather than replace, existing rules.
        primary_concept = concept.get("concept") or {}
        for signal in primary_concept.get("diagnostic_signals", []):
            scores[signal] = scores.get(signal, 0) + max(12, int(float(primary_concept.get("confidence", 0.7)) * 25))

        if mobile_typo_signal(text):
            scores["mobile_repair"] = scores.get("mobile_repair", 0) + 30

        score_company_services(text, company_id, scores)

        if context:
            last = context.get("last_intent")
            if last:
                if last == "mobile_repair" and any(token in text.split() for token in {"celular", "celulares", "movil", "moviles", "telefono", "telefonos", "telefone", "telefones", "pantalla", "apantalla", "tela", "display", "rota", "roto", "roro", "quebrada", "quebrado"}):
                    scores[last] = scores.get(last, 0) + 45
                elif last in scores:
                    scores[last] += 8

        if not scores:
            # Preserve a validated concept even when it does not map cleanly to
            # a service yet; this is the learning/diagnostic path, not a fake intent.
            learning = propose_learning(message, intent=None, language=(context or {}).get("language", "auto"))
            record_learning(learning, company_id=(context or {}).get("company_id"), conversation_id=(context or {}).get("conversation_id"))
            return {"intent": None, "confidence": 0.0, "raw_score": 0, "scores": {}, "concept": concept, "learning": learning}

        intent = max(scores, key=scores.get)
        raw_score = scores[intent]
        confidence = _normalize_confidence(raw_score, scores)
        learning = propose_learning(message, intent=intent, language=(context or {}).get("language", "auto"))
        record_learning(learning, company_id=(context or {}).get("company_id"), conversation_id=(context or {}).get("conversation_id"))
        print("[INTENT SCORES]", scores, "confidence=", confidence, "concept=", primary_concept.get("concept"))
        return {"intent": intent, "confidence": confidence, "raw_score": raw_score, "scores": scores, "concept": concept, "learning": learning}
    except Exception as error:
        print("[INTENT ERROR]", error)
        return {"intent": None, "confidence": 0.0, "raw_score": 0, "scores": {}, "concept": {"known": False, "knowledge_gap": True}, "learning": {"status": "error", "validated": False}}
