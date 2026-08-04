"""
Bitey Intent Service

Intent detection engine.

Uses:
- Local rules
- Knowledge Base learning

No external dependency.
"""


from app.services.knowledge_service import (
    search_knowledge
)



def detect_intent(
    company_id: int,
    message: str
):

    try:

        text = message.lower()


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

                "no prende",
                "nao liga",
                "não liga",
                "pantalla",
                "tela",
                "roto",
                "fallando"

            ],


            "mobile_repair": [

                "celular",
                "telefone",
                "iphone",
                "samsung",
                "motorola"

            ],


            "network_problem": [

                "wifi",
                "internet",
                "conexion",
                "conexão",
                "roteador"

            ]

        }



        best_intent = None
        best_score = 0



        for intent, keywords in intents.items():


            score = 0


            for keyword in keywords:

                if keyword in text:

                    score += 1



            if score > best_score:

                best_score = score
                best_intent = intent



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