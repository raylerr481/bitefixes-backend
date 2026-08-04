"""
Bitey Language Service V1

Detects user language and prepares multilingual responses.

Supported:
- Spanish
- Portuguese
- English
"""


def detect_language(text: str) -> str:

    if not text:
        return "pt"

    text = text.lower()


    spanish_words = [
        "hola",
        "quiero",
        "necesito",
        "mi",
        "esta",
        "está",
        "puedo",
        "cambiar",
        "lento",
        "problema",
        "ayuda"
    ]


    english_words = [
        "hello",
        "need",
        "want",
        "problem",
        "help",
        "computer",
        "laptop"
    ]


    spanish_score = sum(
        1 for word in spanish_words
        if word in text
    )


    english_score = sum(
        1 for word in english_words
        if word in text
    )


    if spanish_score > english_score and spanish_score > 0:
        return "es"


    if english_score > spanish_score:
        return "en"


    return "pt"



def normalize_language(language):

    if language in [
        "es",
        "en",
        "pt"
    ]:
        return language


    return "pt"



def translate_response(
    response:str,
    language:str
):

    """
    Temporary translator layer.

    Later connects with LLM.
    """


    if not response:
        return response


    language = normalize_language(
        language
    )


    if language == "es":

        replacements = {

            "Podemos melhorar":
                "Podemos mejorar",

            "desempenho":
                "rendimiento",

            "memória RAM":
                "memoria RAM",

            "Seu atendimento foi registrado":
                "Su atención fue registrada",

            "Código do ticket":
                "Código del ticket"

        }


        for old,new in replacements.items():
            response = response.replace(
                old,
                new
            )


    elif language == "en":

        replacements = {

            "Podemos melhorar o desempenho do notebook com upgrade de SSD e memória RAM.":
            "We can improve notebook performance with SSD and RAM upgrade.",

            "Seu atendimento foi registrado.":
            "Your request has been registered.",

            "Código do ticket":
            "Ticket code"

        }


        for old,new in replacements.items():
            response=response.replace(
                old,
                new
            )


    return response