"""
Bitey Workflow
Default / Fallback
Multilingual ES / PT / EN

Used when no specialized workflow matches
the customer's request.
"""


def execute(
    message,
    company_id=None,
    customer_id=None,
    service_id=None,
    intent=None,
    customer=None,
    language=None,
    knowledge=None,
    **kwargs
):
    normalized_language = (language or "es").lower()

    if normalized_language.startswith("pt"):
        response = (
            "Obrigado pela mensagem. "
            "Recebi sua solicitação e vou direcioná-la "
            "para análise."
        )

    elif normalized_language.startswith("en"):
        response = (
            "Thank you for your message. "
            "I received your request and will "
            "forward it for review."
        )

    else:
        response = (
            "Gracias por tu mensaje. "
            "Recibí tu solicitud y la enviaré "
            "para su análisis."
        )

    return {
        "success": True,
        "workflow": "default",
        "response": response,
        "ticket": None,
        "ticket_id": None,
        "service_id": service_id,
        "intent": intent,
        "metadata": {
            "company_id": company_id,
            "customer_id": customer_id,
            "language": language or "es",
        },
    }
