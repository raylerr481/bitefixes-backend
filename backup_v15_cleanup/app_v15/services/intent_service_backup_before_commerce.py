"""
Bitey Intent Service

AI intent detection engine.

Priority:

1. Knowledge Base matching
2. Synonyms database
3. Keyword scoring
"""

from app.utils.normalizer import normalize_text
from app.services.knowledge_service import search_knowledge
from app.database.supabase import database


INTENT_ALIASES = {

    "mobile_repair": "mobile_screen_repair",
    "network_support": "network_problem",
    "computer_fix": "computer_repair",
    "camera_installation": "cctv_installation",

}


def normalize_intent(intent):

    if not intent:
        return None

    return INTENT_ALIASES.get(
        intent,
        intent
    )


def calculate_score(text, keywords):

    score = 0

    for keyword, weight in keywords.items():

        if keyword in text:
            score += weight

    return score


def search_synonyms(company_id, text):

    try:

        result = (
            database
            .table("sinonimos_ia")
            .select("*")
            .eq(
                "company_id",
                company_id
            )
            .execute()
        )


        best_intent = None
        best_score = 0


        for item in result.data or []:

            synonym = item.get(
                "sinonimo",
                ""
            )


            if not synonym:
                continue


            synonym = normalize_text(
                synonym
            )


            if synonym in text:

                weight = item.get(
                    "peso",
                    1
                )


                if weight > best_score:

                    best_score = weight

                    best_intent = normalize_intent(
                        item.get("intent")
                    )


        if best_intent:

            return {
                "intent": best_intent,
                "confidence": min(
                    best_score,
                    5
                )
            }


    except Exception as error:

        print(
            "[SYNONYMS ERROR]",
            error
        )


    return None



def detect_intent(
    company_id: int,
    message: str
):

    try:

        text = normalize_text(
            message
        )


        if not text:

            return {
                "intent": None,
                "confidence": 0
            }


        # ==========================
        # KNOWLEDGE BASE
        # ==========================

        knowledge = search_knowledge(
            company_id,
            message
        )


        if knowledge and knowledge.get("found"):

            data = knowledge.get(
                "data",
                {}
            )


            intent = normalize_intent(
                data.get("intent")
            )


            if intent:

                return {
                    "intent": intent,
                    "confidence": 5
                }



        # ==========================
        # DATABASE SYNONYMS
        # ==========================

        synonym_result = search_synonyms(
            company_id,
            text
        )


        if synonym_result:

            return synonym_result



        # ==========================
        # KEYWORD ENGINE
        # ==========================

        intents = {


            "hardware_upgrade": {

                "ssd":5,
                "ram":5,
                "memoria":4,
                "upgrade":5,
                "lento":4,
                "lentitud":4

            },


            "network_problem": {

                "internet":5,
                "wifi":5,
                "wifi no funciona":5,
                "roteador":5,
                "router":5,
                "conexion":4

            },


            "mobile_screen_repair": {

                "celular":5,
                "iphone":5,
                "samsung":4,
                "pantalla":5,
                "tela":5,
                "display":5,
                "screen":5

            },


            "cctv_installation": {

                "camera":5,
                "cameras":5,
                "camara":5,
                "camaras":5,
                "cctv":5,
                "seguranca":4,
                "seguridad":4,
                "dvr":5,
                "nvr":5

            },


            "technical_support": {

                "suporte":5,
                "support":5,
                "soporte":5,
                "remoto":4,
                "remote":4

            },


            "computer_repair": {

                "computador":4,
                "computer":4,
                "notebook":3,
                "travando":5,
                "erro":3

            }

        }



        best_intent = None
        best_score = 0


        for intent, keywords in intents.items():

            score = calculate_score(
                text,
                keywords
            )


            if score > best_score:

                best_score = score
                best_intent = intent



        if best_intent:

            return {

                "intent": best_intent,

                "confidence": min(
                    best_score,
                    5
                )

            }


        return {

            "intent": None,

            "confidence": 0

        }


    except Exception as error:

        print(
            "[BITEY INTENT ERROR]",
            error
        )


        return {

            "intent": None,

            "confidence": 0

        }