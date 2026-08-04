"""
BiteFixes - Bitey Intent Engine V5
Multilingual + Context Aware
"""

import unicodedata
import re

from app.database.supabase import database


# =====================================================
# NORMALIZATION
# =====================================================

def normalize(text):

    if not text:
        return ""

    text = str(text).lower().strip()

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = "".join(
        c for c in text
        if unicodedata.category(c) != "Mn"
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    return " ".join(
        text.split()
    )



# =====================================================
# STATIC RULES
# =====================================================

INTENT_RULES = {

    "ai_assistant":[
        "asistente ia",
        "assistente ia",
        "chatbot",
        "bot whatsapp",
        "automatizar empresa",
        "automatizar whatsapp"
    ],


    "cctv_installation":[
        "camera",
        "cameras",
        "camera seguranca",
        "cameras seguranca",
        "cctv",
        "monitoramento",
        "instalar camera",
        "instalar cameras",
        "security camera"
    ],


    "computer_repair":[
        "no prende",
        "no enciende",
        "nao liga",
        "nao funciona",
        "pantalla negra",
        "tela preta",
        "reparar",
        "arreglar",
        "virus"
    ],


    "hardware_upgrade":[
        "ssd",
        "ram",
        "memoria",
        "upgrade",
        "lento",
        "melhorar",
        "mejorar"
    ]

}



# =====================================================
# DATABASE
# =====================================================

def get_synonyms():

    try:

        result = (
            database
            .table("sinonimos_ia")
            .select("*")
            .execute()
        )

        return result.data or []


    except Exception as error:

        print(
            "[SYNONYMS ERROR]",
            error
        )

        return []



# =====================================================
# WORD MATCH
# =====================================================

def keyword_match(keyword, text):

    keyword = normalize(keyword)

    text_words = set(
        text.split()
    )


    keyword_words = (
        keyword.split()
    )


    matches = 0


    for word in keyword_words:

        if word in text_words:

            matches += 1


    return matches == len(keyword_words)



# =====================================================
# DETECTOR
# =====================================================

def detect_intent(
    message,
    company_id=None,
    context=None
):

    try:

        text = normalize(message)

        scores = {}


        # DATABASE SYNONYMS

        for item in get_synonyms():

            keyword = item.get(
                "keyword",
                ""
            )


            intent = item.get(
                "intent"
            )


            weight = item.get(
                "weight",
                1
            )


            if keyword_match(
                keyword,
                text
            ):

                scores[intent] = (
                    scores.get(intent,0)
                    +
                    weight * 10
                )



        # STATIC RULES

        for intent, words in INTENT_RULES.items():

            for word in words:

                if keyword_match(
                    word,
                    text
                ):

                    scores[intent] = (
                        scores.get(intent,0)
                        +
                        20
                    )



        # CONTEXT

        if context:

            last = context.get(
                "last_intent"
            )

            if last in scores:

                scores[last] += 5



        if not scores:

            return {
                "intent":None,
                "confidence":0
            }



        intent = max(
            scores,
            key=scores.get
        )


        confidence = scores[intent]


        print(
            "[INTENT SCORES]",
            scores
        )


        return {

            "intent":intent,

            "confidence":confidence

        }



    except Exception as error:

        print(
            "[INTENT ERROR]",
            error
        )

        return {

            "intent":None,

            "confidence":0

        }