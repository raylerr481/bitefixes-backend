"""
Bitey Language Service V2

Detects:

- Spanish
- Portuguese
- English
"""


def detect_language(text: str) -> str:

    if not text:
        return "es"


    text = text.lower()


    spanish_words = [
        "hola",
        "quiero",
        "necesito",
        "necesita",
        "mi",
        "mis",
        "esta",
        "está",
        "tengo",
        "puedo",
        "cambiar",
        "problema",
        "ayuda",
        "instalar",
        "camaras",
        "cámaras",
        "tienda",
        "empresa",
        "computadora",
        "ordenador"
    ]


    portuguese_words = [
        "ola",
        "quero",
        "preciso",
        "minha",
        "meu",
        "tenho",
        "problema",
        "ajuda",
        "instalar",
        "câmeras",
        "loja",
        "empresa",
        "computador"
    ]


    english_words = [
        "hello",
        "need",
        "want",
        "problem",
        "help",
        "computer",
        "laptop",
        "install"
    ]


    scores = {

        "es":
            sum(
                1
                for word in spanish_words
                if word in text
            ),

        "pt":
            sum(
                1
                for word in portuguese_words
                if word in text
            ),

        "en":
            sum(
                1
                for word in english_words
                if word in text
            )

    }


    language = max(
        scores,
        key=scores.get
    )


    # Si hay empate o no hay señales
    if scores[language] == 0:

        return "es"


    return language



def normalize_language(language):

    if language:

        language = language.lower()


    if language in [
        "es",
        "pt",
        "en"
    ]:
        return language


    return "es"



def translate_response(
    response: str,
    language: str
):

    return response