"""Bitey computer-repair workflow.

Diagnostic-first: identifying a broken computer starts a diagnostic flow and
must not create a ticket until the user explicitly requests repair/quote after
an actionable diagnosis.
"""


def execute(
    message,
    company_id=None,
    customer_id=None,
    service_id=None,
    intent=None,
    customer=None,
    language=None,
    business_context=None,
    knowledge=None,
    **kwargs,
):
    normalized_language = (language or "es").lower()

    if normalized_language.startswith("pt"):
        response = "Vamos fazer o diagnóstico do seu computador. O que está acontecendo: não liga, está lento, não inicia, apresenta erro ou outro problema?"
    elif normalized_language.startswith("en"):
        response = "Let's diagnose your computer. What is happening: it won't turn on, is slow, won't boot, shows an error, or something else?"
    else:
        response = "Vamos a hacer el diagnóstico de tu computadora. ¿Qué sucede: no enciende, está lenta, no inicia, muestra un error u otro problema?"

    return {
        "success": True,
        "workflow": "computer_repair",
        "diagnostic_pending": True,
        "response": response,
        "metadata": {
            "company_id": company_id,
            "customer_id": customer_id,
            "service_id": service_id,
            "intent": intent,
            "language": language or "es",
            "diagnostic_stage": "symptom_collection",
        },
    }
