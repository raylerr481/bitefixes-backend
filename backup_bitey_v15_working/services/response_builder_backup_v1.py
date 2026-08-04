"""
Bitey Response Builder V15

Responsible for:
- Building final customer response
- Multilingual responses
- Knowledge answers
- Service information
- Ticket information
"""

from app.services.language_service import (
    detect_language,
    normalize_language,
    translate_response
)


# =====================================================
# BUILD RESPONSE
# =====================================================

def build_response(
    knowledge=None,
    service=None,
    ticket=None,
    context=None,
    channel="website",
    message="",
    language=None
):

    """
    Creates final Bitey customer response.
    """


    if not language:

        language = detect_language(
            message
        )


    language = normalize_language(
        language
    )


    parts = []



    # =================================================
    # KNOWLEDGE ANSWER
    # =================================================

    if knowledge:


        answer = knowledge.get(
            "answer"
        )


        if answer:

            parts.append(
                translate_response(
                    answer,
                    language
                )
            )



    # =================================================
    # SERVICE
    # =================================================

    if service:


        name = service.get(
            "name"
        )


        if name:


            if language == "pt":

                parts.append(
                    f"Serviço recomendado: {name}"
                )


            elif language == "en":

                parts.append(
                    f"Recommended service: {name}"
                )


            else:

                parts.append(
                    f"Servicio recomendado: {name}"
                )



    # =================================================
    # TICKET
    # =================================================

    if ticket:


        code = (

            ticket.get(
                "ticket_code"
            )

            or

            ticket.get(
                "codigo_ticket"
            )

        )



        if language == "pt":


            parts.append(
                "Sua solicitação foi registrada."
            )


            if code:

                parts.append(
                    f"Código do chamado: {code}"
                )


            parts.append(
                "Status: aberto"
            )



        elif language == "en":


            parts.append(
                "Your request has been registered."
            )


            if code:

                parts.append(
                    f"Ticket code: {code}"
                )


            parts.append(
                "Status: open"
            )



        else:


            parts.append(
                "Su solicitud fue registrada."
            )


            if code:

                parts.append(
                    f"Código del ticket: {code}"
                )


            parts.append(
                "Estado: abierto"
            )



    # =================================================
    # FALLBACK
    # =================================================

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