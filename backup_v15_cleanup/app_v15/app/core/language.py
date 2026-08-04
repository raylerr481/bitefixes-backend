"""
Bitey Language Normalizer

Normalizes customer messages before intent detection.

Handles:
- Portuguese variations
- Spanish variations
- common technical synonyms
"""


def normalize_message(
    message: str
):

    text = message.lower().strip()


    replacements = {


        # Devices

        "laptop":
            "notebook",

        "portatil":
            "notebook",

        "portátil":
            "notebook",

        "ordenador":
            "computador",

        "computadora":
            "computador",



        # Performance

        "pesado":
            "lento",

        "pesada":
            "lenta",

        "muy lento":
            "lento",

        "muito lento":
            "lento",

        "travando":
            "trava",

        "congelando":
            "trava",



        # Screen

        "pantalla":
            "tela",

        "display":
            "tela",

        "vidro":
            "tela",



        # Battery

        "bateria ruim":
            "bateria",

        "se acaba rápido":
            "descarrega",

        "dura poco":
            "descarrega",



        # Network

        "wi-fi":
            "wifi",

        "sem internet":
            "internet",

        "no conecta":
            "rede",

        "não conecta":
            "rede",

        "nao conecta":
            "rede",

    }


    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )


    return text