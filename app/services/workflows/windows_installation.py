"""
Bitey Workflow
Windows Installation
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
            "Realizamos instalação e configuração do Windows, "
            "incluindo preparação do sistema, instalação de drivers "
            "e configuração inicial."
        )

    elif normalized_language.startswith("en"):
        response = (
            "We perform Windows installation and configuration, "
            "including system preparation, driver installation, "
            "and initial setup."
        )

    else:
        response = (
            "Realizamos instalación y configuración de Windows, "
            "incluyendo preparación del sistema, instalación de "
            "controladores y configuración inicial."
        )

    return {
        "success": True,
        "workflow": "windows_installation",
        "response": response,
        "metadata": {
            "company_id": company_id,
            "customer_id": customer_id,
            "service_id": service_id,
            "intent": intent,
            "language": language or "es",
        },
    }
