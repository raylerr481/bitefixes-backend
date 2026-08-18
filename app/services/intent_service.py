"""
BiteFixes - Bitey Intent Engine V6
Multilingual + Context Aware + Company Service Aware

Intent detection remains deterministic and dependency-free. Company services
are used as a second semantic signal so new tenant services can participate
without hard-coding every service in Python.
"""

import re
import unicodedata

from app.database.supabase import database


# =====================================================
# NORMALIZATION
# =====================================================

def normalize(text):
    if not text:
        return ""

    text = str(text).lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


# =====================================================
# LEGACY / HIGH PRECISION RULES
# =====================================================

INTENT_RULES = {
    "ai_assistant": [
        "asistente ia", "assistente ia", "chatbot", "bot whatsapp",
        "automatizar empresa", "automatizar whatsapp",
    ],
    "cctv_installation": [
        "camera", "cameras", "camera seguranca", "cameras seguranca",
        "cctv", "monitoramento", "instalar camera", "instalar cameras",
        "security camera",
    ],
    "computer_repair": [
        "no prende", "no enciende", "nao liga", "nao funciona",
        "pantalla negra", "tela preta", "reparar", "arreglar", "virus",
    ],
    "hardware_upgrade": [
        "ssd", "ram", "memoria", "upgrade", "lento", "melhorar", "mejorar",
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
        "reparar celular", "arreglar celular", "consertar celular",
        "reparar telefone", "consertar telefone", "mobile repair",
        "celular quebrado", "telefono roto",
    ],
    "windows_installation": [
        "instalar windows", "instalacion windows", "instalacao windows",
        "formatar computador", "formatar notebook", "formatear pc",
    ],
}


# =====================================================
# DATABASE
# =====================================================

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


# =====================================================
# MATCHING
# =====================================================

def keyword_match(keyword, text):
    keyword = normalize(keyword)
    if not keyword or not text:
        return False

    text_words = set(text.split())
    keyword_words = keyword.split()
    return all(word in text_words for word in keyword_words)


def phrase_score(phrase, text):
    phrase = normalize(phrase)
    if not phrase:
        return 0

    if keyword_match(phrase, text):
        # Longer phrases are more discriminating than single words.
        return 18 + min(len(phrase.split()), 4) * 2

    return 0


# =====================================================
# COMPANY SERVICE SIGNAL
# =====================================================

def score_company_services(text, company_id, scores):
    """Use the tenant's catalog as a dynamic intent signal."""
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


# =====================================================
# DETECTOR
# =====================================================

def detect_intent(message, company_id=None, context=None):
    try:
        text = normalize(message)
        scores = {}

        # 1. Tenant knowledge / learned synonyms.
        for item in get_synonyms():
            keyword = item.get("keyword", "")
            intent = item.get("intent")
            weight = item.get("weight", 1) or 1

            if intent and keyword_match(keyword, text):
                scores[intent] = scores.get(intent, 0) + weight * 10

        # 2. Explicit high-precision compatibility rules.
        for intent, words in INTENT_RULES.items():
            for word in words:
                match_score = phrase_score(word, text)
                if match_score:
                    scores[intent] = scores.get(intent, 0) + match_score

        # 3. Current company's actual service catalog.
        score_company_services(text, company_id, scores)

        # 4. Conversation context only reinforces an already plausible intent.
        if context:
            last = context.get("last_intent")
            if last in scores:
                scores[last] += 5

        if not scores:
            return {"intent": None, "confidence": 0}

        intent = max(scores, key=scores.get)
        confidence = scores[intent]

        print("[INTENT SCORES]", scores)

        return {
            "intent": intent,
            "confidence": confidence,
            "scores": scores,
        }

    except Exception as error:
        print("[INTENT ERROR]", error)
        return {"intent": None, "confidence": 0}
