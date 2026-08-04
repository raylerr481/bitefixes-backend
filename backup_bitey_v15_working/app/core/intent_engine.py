from app.core.language import normalize_message

INTENT_RULES = {

    "mobile_screen_repair": [

        "pantalla",
        "display",
        "vidrio",
        "rota",
        "roto",
        "quebrada",
        "quebrado",
        "celular",
        "movil",
        "móvil",
        "iphone",
        "samsung"

    ],

    "hardware_upgrade": [

        "lenta",
        "lento",
        "notebook",
        "laptop",
        "ssd",
        "ram",
        "memoria",
        "rendimiento",
        "performance"

    ],

    "network_support": [

        "wifi",
        "wi-fi",
        "internet",
        "router",
        "red",
        "conexion",
        "conexión"

    ],

    "computer_repair": [

        "computador",
        "computadora",
        "ordenador",
        "pc",
        "cpu",
        "no funciona",
        "no enciende"

    ]

}


def detect_intent(message):

    """
    Devuelve:
        intent
        confidence
    """

    text = normalize_message(message).lower()

    best_intent = None
    best_score = 0

    for intent, keywords in INTENT_RULES.items():

        score = 0

        for keyword in keywords:

            if keyword in text:
                score += 1

        if score > best_score:
            best_score = score
            best_intent = intent

    if best_score == 0:
        return None, 0

    confidence = min(
        1,
        best_score / 3
    )

    return best_intent, confidence