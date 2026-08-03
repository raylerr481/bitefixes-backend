"""
Bitey Response Builder

Responsible for generating final customer responses.

Features:
- Knowledge base answers
- Service recommendation
- Ticket information
- Basic language detection
"""


def detect_language(message: str = "") -> str:
    """
    Detect customer language.

    Returns:
        es -> Spanish
        pt -> Portuguese
        en -> English
    """

    text = (message or "").lower()


    portuguese_keywords = [
        "quero",
        "preciso",
        "computador",
        "celular",
        "suporte",
        "empresa",
        "ajuda",
        "instalação",
        "instalacao",
        "manutenção",
        "manutencao",
    ]


    spanish_keywords = [
        "quiero",
        "necesito",
        "computadora",
        "celular",
        "soporte",
        "empresa",
        "ayuda",
        "instalación",
        "instalacion",
    ]


    english_keywords = [
        "want",
        "need",
        "computer",
        "support",
        "company",
        "help",
        "assistant",
    ]


    scores = {
        "pt": 0,
        "es": 0,
        "en": 0,
    }


    for word in portuguese_keywords:

        if word in text:
            scores["pt"] += 1


    for word in spanish_keywords:

        if word in text:
            scores["es"] += 1


    for word in english_keywords:

        if word in text:
            scores["en"] += 1


    language = max(
        scores,
        key=scores.get
    )


    if scores[language] == 0:

        return "es"


    return language



def build_response(
    knowledge=None,
    service=None,
    ticket=None,
    context=None,
    channel="website",
    message=""
):
    """
    Build final Bitey customer response.
    """


    language = detect_language(
        message
    )


    parts = []


    # ==========================================
    # KNOWLEDGE ANSWER
    # ==========================================

    if knowledge:

        answer = knowledge.get(
            "answer"
        )


        if answer:

            parts.append(
                answer
            )


    # ==========================================
    # SERVICE INFORMATION
    # ==========================================

    if service:

        service_name = service.get(
            "name"
        )


        if language == "pt":

            parts.append(
                f"Serviço recomendado: {service_name}"
            )


        elif language == "en":

            parts.append(
                f"Recommended service: {service_name}"
            )


        else:

            parts.append(
                f"Servicio recomendado: {service_name}"
            )


    # ==========================================
    # TICKET INFORMATION
    # ==========================================

    if ticket:

        ticket_code = (
            ticket.get("ticket_code")
            or
            ticket.get("codigo_ticket")
        )


        if language == "pt":

            parts.append(
                "Sua solicitação foi registrada."
            )


            if ticket_code:

                parts.append(
                    f"Código do chamado: {ticket_code}"
                )


            parts.append(
                "Estado: aberto"
            )


        elif language == "en":

            parts.append(
                "Your request has been registered."
            )


            if ticket_code:

                parts.append(
                    f"Ticket code: {ticket_code}"
                )


            parts.append(
                "Status: open"
            )


        else:

            parts.append(
                "Solicitud registrada."
            )


            if ticket_code:

                parts.append(
                    f"Código del ticket: {ticket_code}"
                )


            parts.append(
                "Estado: abierto"
            )


    # ==========================================
    # EMPTY RESPONSE FALLBACK
    # ==========================================

    if not parts:

        if language == "pt":

            return (
                "Como posso ajudar você?"
            )


        if language == "en":

            return (
                "How can I help you?"
            )


        return (
            "¿Cómo puedo ayudarte?"
        )


    return "\n\n".join(parts)