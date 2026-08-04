"""
Bitey Intent Service

Context aware intent detection engine.

Flow:

Message
   |
Normalize text
   |
Priority intent rules
   |
Knowledge Base fallback
   |
Intent + Confidence

"""

from app.utils.normalizer import (
    normalize_text
)

from app.services.knowledge_service import (
    search_knowledge
)



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


        #
        # ==================================
        # PRIORITY INTENTS
        # ==================================
        # More specific contexts first
        #


        # -------------------------------
        # NETWORK
        # -------------------------------

        network_keywords = [

            "internet",
            "wifi",
            "wifi",
            "rede",
            "roteador",
            "router",
            "conexao",
            "conectar",
            "conecta",
            "sem internet"

        ]


        if any(
            keyword in text
            for keyword in network_keywords
        ):

            return {

                "intent": "network_problem",

                "confidence": 5

            }



        # -------------------------------
        # MOBILE
        # -------------------------------

        mobile_keywords = [

            "celular",
            "telefone",
            "iphone",
            "samsung",
            "motorola",
            "smartphone"

        ]


        if any(
            keyword in text
            for keyword in mobile_keywords
        ):

            return {

                "intent": "mobile_repair",

                "confidence": 5

            }



        # -------------------------------
        # HARDWARE UPGRADE
        # -------------------------------

        upgrade_keywords = [

            "lento",
            "lentidao",
            "ram",
            "memoria",
            "ssd",
            "upgrade",
            "melhorar",
            "desempenho",
            "performance"

        ]


        if any(
            keyword in text
            for keyword in upgrade_keywords
        ):

            return {

                "intent": "hardware_upgrade",

                "confidence": 5

            }



        # -------------------------------
        # COMPUTER REPAIR
        # -------------------------------

        repair_keywords = [

            "nao liga",
            "nao inicia",
            "travando",
            "erro",
            "tela",
            "pantalla",
            "quebrado",
            "falha"

        ]


        if any(
            keyword in text
            for keyword in repair_keywords
        ):

            return {

                "intent": "computer_repair",

                "confidence": 5

            }



        #
        # ==================================
        # KNOWLEDGE BASE FALLBACK
        # ==================================
        #

        knowledge = search_knowledge(

            company_id,

            message

        )


        if knowledge:


            data = knowledge.get(

                "data",

                {}

            )


            kb_intent = data.get(

                "intent"

            )


            if kb_intent:


                return {

                    "intent": kb_intent,

                    "confidence": 2

                }



        #
        # ==================================
        # NO MATCH
        # ==================================
        #

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