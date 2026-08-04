"""
Bitey Intent Service

Intent detection engine.

Features:

- Multilingual detection
- Text normalization
- Weighted keywords
- Knowledge Base reinforcement
"""


from app.services.knowledge_service import (
    search_knowledge
)

from app.utils.normalizer import (
    normalize_text
)



INTENT_RULES = {


    "hardware_upgrade": {

        "keywords": {

            "ssd": 4,
            "ram": 4,
            "memoria": 3,
            "memory": 3,
            "upgrade": 4,
            "actualizar": 3,
            "aumentar": 2,
            "lento": 2,
            "lentitud": 2,
            "slow": 2,
            "performance": 2,
            "desempenho": 2,
            "desempeño": 2

        }

    },


    "computer_repair": {

        "keywords": {

            "nao liga": 5,
            "no liga": 5,
            "not turn": 5,
            "pantalla": 3,
            "tela": 3,
            "screen": 3,
            "roto": 2,
            "quebrado": 2,
            "falha": 2,
            "problema": 1

        }

    },


    "mobile_repair": {

        "keywords": {

            "celular": 4,
            "telefone": 3,
            "iphone": 4,
            "samsung": 4,
            "motorola": 4,
            "mobile": 3

        }

    },


    "network_problem": {

        "keywords": {

            "wifi": 4,
            "internet": 4,
            "roteador": 3,
            "router": 3,
            "conexion": 3,
            "conexao": 3,
            "network": 3

        }

    }

}




def detect_intent(
    company_id: int,
    message: str
):

    try:


        text = normalize_text(
            message
        )



        best_intent = None

        best_score = 0



        for intent, data in INTENT_RULES.items():


            score = 0


            for keyword, weight in data["keywords"].items():


                if keyword in text:

                    score += weight



            if score > best_score:

                best_score = score

                best_intent = intent



        # ==========================
        # KNOWLEDGE BASE BOOST
        # ==========================


        knowledge = search_knowledge(

            company_id,

            message

        )


        if knowledge:


            kb_data = knowledge.get(
                "data",
                {}
            )


            kb_intent = kb_data.get(
                "intent"
            )


            if kb_intent:

                best_intent = kb_intent

                best_score += 3



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
            "[INTENT SERVICE ERROR]",
            error
        )


        return {

            "intent": None,

            "confidence": 0

        }