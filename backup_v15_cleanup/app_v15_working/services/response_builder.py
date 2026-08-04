"""
Bitey Response Builder V8

Responsible for:
- Creating final AI responses
- Language adaptation
- Ticket confirmation
- Multi-channel output
"""


def build_response(
    knowledge=None,
    language="pt",
    ticket=None,
    fallback=None
):

    try:

        response = ""


        # ===============================
        # KNOWLEDGE ANSWER
        # ===============================

        if knowledge:

            response = knowledge.get(
                "answer",
                ""
            )


        # ===============================
        # FALLBACK
        # ===============================

        if not response:

            response = fallback or (
                "Obrigado por contactar Bitey. "
                "Sua solicitação foi recebida."
            )



        # ===============================
        # TRANSLATION PT -> ES
        # ===============================

        if language == "es":

            replacements = {

                "Podemos melhorar":
                    "Podemos mejorar",

                "o desempenho":
                    "el rendimiento",

                "do notebook":
                    "del notebook",

                "com upgrade":
                    "con una mejora",

                "de SSD":
                    "de SSD",

                "e memória RAM":
                    "y memoria RAM",

                "Sua solicitação":
                    "Tu solicitud",

                "foi recebida":
                    "fue recibida",

                "Seu atendimento":
                    "Tu atención",

                "foi registrado":
                    "fue registrado"

            }


            for old, new in replacements.items():

                response = response.replace(
                    old,
                    new
                )



        # ===============================
        # TICKET
        # ===============================

        if ticket:


            ticket_code = ticket.get(
                "ticket_code"
            )


            if ticket_code:


                if language == "es":

                    response += (

                        "\n\nTu solicitud fue registrada."

                        f"\nCódigo del ticket: {ticket_code}"

                    )

                else:

                    response += (

                        "\n\nSeu atendimento foi registrado."

                        f"\nCódigo do ticket: {ticket_code}"

                    )



        return response.strip()



    except Exception as error:


        print(
            "[RESPONSE BUILDER ERROR]",
            error
        )


        return (
            "Erro ao gerar resposta."
        )