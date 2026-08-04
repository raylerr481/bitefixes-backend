"""
Bitey Intent Service

Intent detection engine.

Priority:

1. Text normalization
2. Local intent rules
3. Knowledge Base reinforcement
4. Confidence scoring

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


        intents = {


            "hardware_upgrade": [

                "lento",
                "lentitud",
                "ram",
                "ssd",
                "memoria",
                "upgrade",
                "melhorar",
                "desempenho",
                "performance"

            ],


            "computer_repair": [

                "nao liga",
                "nao inicia",
                "nao funciona",
                "travando",
                "erro",
                "tela",
                "pantalla",
                "quebrado",
                "falhando"

            ],


            "mobile_repair": [

                "celular",
                "telefone",
                "iphone",
                "samsung",
                "motorola",
                "smartphone"

            ],


            "network_problem": [

                "internet",
                "wifi",
                "rede",
                "roteador",
                "conexao",
                "conecta",
                "sem internet",
                "nao conecta"

            ]

        }


        scores = {}


        for intent, keywords in intents.items():

            score = 0


            for keyword in keywords:

                if keyword in text:

                    score += 1


            scores[intent] = score



        best_intent = max(
            scores,
            key=scores.get
        )


        best_score = scores[best_intent]


        if best_score == 0:

            best_intent = None



        #
        # Knowledge Base reinforcement
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


            #
            # Only reinforce
            # Do not overwrite strong detection
            #

            if kb_intent and not best_intent:

                best_intent = kb_intent

                best_score += 2



        if best_intent:

            return {

                "intent": best_intent,

                "confidence": best_score

            }


        return {

            "intent": None,

            "confidence": 0

        }



    except Exception as error:


        print(
            "[INTENT ERROR]",
            error
        )


        return {

            "intent": None,

            "confidence": 0

        }