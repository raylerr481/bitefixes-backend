"""
Bitey Workflow
Hardware Upgrade
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
            "Realizamos atualização de hardware, "
            "instalação de SSD, expansão de memória RAM "
            "e melhorias de desempenho."
        )

    elif normalized_language.startswith("en"):
        response = (
            "We perform hardware upgrades, "
            "SSD installation, RAM upgrades, "
            "and performance improvements."
        )

    else:
        response = (
            "Realizamos actualización de hardware, "
            "instalación de SSD, ampliación de memoria RAM "
            "y mejoras de rendimiento."
        )

    return {
        "success": True,
        "workflow": "hardware_upgrade",
        "response": response,
        "metadata": {
            "company_id": company_id,
            "customer_id": customer_id,
            "service_id": service_id,
            "intent": intent,
            "language": language or "es",
        },
    }
