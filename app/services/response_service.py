"""
BiteFixes Response Service

Generates Bitey's final answer.
"""


def generate_response(
    intent=None,
    knowledge=None,
    service=None,
    ticket_id=None
):


    response = None


    # Knowledge first

    if knowledge:

        response = knowledge.get(
            "answer"
        )



    # Intent fallback

    if not response:


        if intent == "ai_assistant":

            response = (
                "Creamos asistentes inteligentes "
                "personalizados para empresas, "
                "automatización de WhatsApp "
                "y optimización de procesos."
            )


        elif service:

            response = (
                "Podemos ayudarte con "
                + service.get(
                    "name",
                    "nuestro servicio"
                )
            )


        else:

            response = (
                "Gracias por contactar BiteFixes. "
                "Estoy revisando tu solicitud."
            )



    if service:

        response += (
            "\n\nServicio: "
            + service.get(
                "name",
                ""
            )
        )



    if ticket_id:

        response += (
            "\nTicket asociado: #"
            + str(ticket_id)
        )


    return response