"""
Bitey Workflow
Computer Repair
Multilingual
"""


def execute(
    message,
    company_id=None,
    customer_id=None,
    service_id=None,
    intent=None,
    customer=None,
    language=None
):

    normalized_language = (language or "es").lower()

    if normalized_language.startswith("pt"):

        response = (
            "Vamos verificar o seu computador e realizar "
            "o diagnóstico técnico necessário."
        )

    elif normalized_language.startswith("en"):

        response = (
            "We will inspect your computer and perform "
            "the necessary technical diagnosis."
        )

    else:

        response = (
            "Vamos a revisar tu equipo y realizar "
            "el diagnóstico técnico correspondiente."
        )

    return {

        "success": True,

        "workflow":
            "computer_repair",

        "response":
            response,

        "metadata": {

            "company_id": company_id,
            "customer_id": customer_id,
            "service_id": service_id,
            "intent": intent,
            "language": language

        }

    }
