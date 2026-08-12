"""
Bitey Workflow
Mobile Repair
Multilingual ES / PT / EN
"""


def execute(
    message,
    company_id=None,
    customer_id=None,
    service_id=None,
    intent=None,
    customer=None,
    language=None,
    **kwargs
):
    normalized_language = (language or "es").lower()

    if normalized_language.startswith("pt"):
        response = (
            "Podemos realizar o diagnóstico e reparo "
            "do seu celular. Vamos avaliar o problema "
            "e informar o orçamento."
        )

    elif normalized_language.startswith("en"):
        response = (
            "We can diagnose and repair your mobile phone. "
            "We will evaluate the problem and provide "
            "a repair estimate."
        )

    else:
        response = (
            "Podemos realizar el diagnóstico y reparación "
            "de tu celular. Evaluaremos el problema "
            "y te informaremos el presupuesto."
        )

    return {
        "success": True,
        "workflow": "mobile_repair",
        "response": response,
        "metadata": {
            "company_id": company_id,
            "customer_id": customer_id,
            "service_id": service_id,
            "intent": intent,
            "language": language or "es",
        },
    }
