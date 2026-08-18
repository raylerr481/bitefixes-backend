"""Bitey Response Builder V6."""


def language_text(language, data):
    language = (language or "es").lower()
    if language.startswith("pt"):
        return data.get("pt", data.get("es"))
    if language.startswith("en"):
        return data.get("en", data.get("es"))
    return data.get("es")


def _customer_name(customer_name):
    name = str(customer_name or "").strip()
    if not name or name.lower() in {"customer", "cliente", "customer name"}:
        return ""
    return name


def build_ticket_response(ticket=None, language="es", customer_name=None):
    if not ticket or not isinstance(ticket, dict):
        return ""

    ticket_code = ticket.get("ticket_code") or ticket.get("codigo_ticket") or ticket.get("code") or ticket.get("id")
    name = _customer_name(customer_name)
    messages = {
        "es": f"{name}, tu solicitud fue registrada correctamente." if name else "Tu solicitud fue registrada correctamente.",
        "pt": f"{name}, sua solicitação foi registrada corretamente." if name else "Sua solicitação foi registrada corretamente.",
        "en": f"{name}, your request has been registered successfully." if name else "Your request has been registered successfully.",
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
        return response.get("response") or response.get("message") or response.get("text") or ""
    return str(response)


def _personalize(text, language, customer_name):
    name = _customer_name(customer_name)
    if not name or not text:
        return text
    if text.lstrip().lower().startswith(name.lower() + ","):
        return text
    # Keep the name natural without forcing it into every sentence.
    return f"{name}, {text[0].lower() + text[1:] if len(text) > 1 else text}"


def build_final_response(decision=None, ticket=None, knowledge=None, language="es", customer_name=None):
    if not decision:
        return language_text(language, {
            "es": "No pude procesar tu solicitud.",
            "pt": "Não consegui processar sua solicitação.",
            "en": "I could not process your request.",
        })

    response = normalize_response(decision.get("response"))
    if not response:
        response = language_text(language, {
            "es": "Solicitud recibida.",
            "pt": "Solicitação recebida.",
            "en": "Request received.",
        })

    response = _personalize(response, language, customer_name)
    ticket_text = build_ticket_response(ticket, language, customer_name)
    if ticket_text:
        response += "\n\n" + ticket_text
    return response


def build_response(decision=None, ticket=None, knowledge=None, language="es", customer_name=None, **kwargs):
    return build_final_response(
        decision=decision,
        ticket=ticket,
        knowledge=knowledge,
        language=language,
        customer_name=customer_name,
    )
