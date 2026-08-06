"""
Bitey Response Builder V2

Responsable de construir la respuesta final enviada al cliente.

Soporta:
- Español
- Portugués
- Inglés
- Tickets
- Knowledge base
- Sales
- Web
- WhatsApp
- App

Compatible con Bitey Core V15
"""


def get_language_text(language, texts):

    language = (language or "es").lower()

    if language.startswith("pt"):
        return texts.get("pt", texts.get("es"))

    if language.startswith("en"):
        return texts.get("en", texts.get("es"))

    return texts.get("es")


# -------------------------------------------------
# Ticket response
# -------------------------------------------------

def build_ticket_response(
    ticket=None,
    language="es",
    customer_name=None
):

    if not ticket:
        return ""


    ticket_code = None


    if isinstance(ticket, dict):

        ticket_code = (
            ticket.get("ticket_code")
            or ticket.get("codigo_ticket")
            or ticket.get("id")
        )


    messages = {

        "es":
        "Tu solicitud fue registrada correctamente.",

        "pt":
        "Sua solicitação foi registrada corretamente.",

        "en":
        "Your request has been registered successfully."

    }


    response = get_language_text(
        language,
        messages
    )


    if ticket_code:


        codes = {

            "es":
            f"\n\nCódigo del ticket: {ticket_code}",

            "pt":
            f"\n\nCódigo do chamado: {ticket_code}",

            "en":
            f"\n\nTicket code: {ticket_code}"

        }


        response += codes.get(
            language,
            codes["es"]
        )


    return response



# -------------------------------------------------
# Sales response
# -------------------------------------------------

def build_sales_response(
    response,
    ticket=None,
    language="es"
):


    if isinstance(response, dict):

        message = response.get(
            "response",
            ""
        )

    else:

        message = str(response or "")



    ticket_message = build_ticket_response(
        ticket,
        language
    )


    if ticket_message:

        return (
            message
            +
            "\n\n"
            +
            ticket_message
        )


    return message



# -------------------------------------------------
# Knowledge response
# -------------------------------------------------

def build_knowledge_response(
    knowledge,
    language="es"
):


    if not knowledge:
        return ""


    if isinstance(knowledge, dict):

        return (
            knowledge.get("answer")
            or
            knowledge.get("content")
            or
            knowledge.get("response")
            or
            ""
        )


    return str(knowledge)



# -------------------------------------------------
# FINAL BUILDER
# -------------------------------------------------

def build_final_response(
    decision=None,
    ticket=None,
    knowledge=None,
    language="es"
):


    if not decision:


        return get_language_text(
            language,
            {

                "es":
                "No pude procesar tu solicitud.",

                "pt":
                "Não consegui processar sua solicitação.",

                "en":
                "I could not process your request."

            }
        )



    action = decision.get(
        "action"
    )


    response = decision.get(
        "response"
    )



    if action == "sales":


        return build_sales_response(
            response,
            ticket,
            language
        )



    if knowledge:


        knowledge_response = build_knowledge_response(
            knowledge,
            language
        )


        if knowledge_response:

            return knowledge_response



    if isinstance(response,str):

        return response



    if isinstance(response,dict):

        return response.get(
            "response",
            ""
        )



    return get_language_text(
        language,
        {

            "es":
            "Solicitud recibida.",

            "pt":
            "Solicitação recebida.",

            "en":
            "Request received."

        }
    )



# -------------------------------------------------
# Compatibilidad Core V15
# -------------------------------------------------

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