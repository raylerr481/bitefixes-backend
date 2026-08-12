"""
Bitey Response Builder V5
Multilingual response builder
"""


def language_text(language, data):

    language = (language or "es").lower()

    if language.startswith("pt"):
        return data.get("pt", data.get("es"))

    if language.startswith("en"):
        return data.get("en", data.get("es"))

    return data.get("es")


def build_ticket_response(ticket=None, language="es"):

    if not ticket:
        return ""

    if not isinstance(ticket, dict):
        return ""

    ticket_code = (
        ticket.get("ticket_code")
        or ticket.get("codigo_ticket")
        or ticket.get("code")
        or ticket.get("id")
    )

    messages = {
        "es": "Tu solicitud fue registrada correctamente.",
        "pt": "Sua solicitação foi registrada corretamente.",
        "en": "Your request has been registered successfully."
    }

    response = language_text(language, messages)

    if ticket_code:

        normalized_language = (language or "es").lower()

        if normalized_language.startswith("pt"):
            response += f"\n\nCódigo do chamado: {ticket_code}"

        elif normalized_language.startswith("en"):
            response += f"\n\nTicket code: {ticket_code}"

        else:
            response += f"\n\nCódigo del ticket: {ticket_code}"

    return response


def normalize_response(response):

    if response is None:
        return ""

    if isinstance(response, str):
        return response

    if isinstance(response, dict):
        return (
            response.get("response")
            or response.get("message")
            or response.get("text")
            or ""
        )

    return str(response)


def build_final_response(
    decision=None,
    ticket=None,
    knowledge=None,
    language="es"
):

    if not decision:
        return language_text(
            language,
            {
                "es": "No pude procesar tu solicitud.",
                "pt": "Não consegui processar sua solicitação.",
                "en": "I could not process your request."
            }
        )

    response = normalize_response(
        decision.get("response")
    )

    if not response:
        response = language_text(
            language,
            {
                "es": "Solicitud recibida.",
                "pt": "Solicitação recebida.",
                "en": "Request received."
            }
        )

    ticket_text = build_ticket_response(
        ticket,
        language
    )

    if ticket_text:
        response += "\n\n" + ticket_text

    return response


def build_response(
    decision=None,
    ticket=None,
    knowledge=None,
    language="es",
    **kwargs
):

    return build_final_response(
        decision=decision,
        ticket=ticket,
        knowledge=knowledge,
        language=language
    )
