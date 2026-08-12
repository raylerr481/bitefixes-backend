"""
Bitey Workflow
Network Support
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
            "Podemos realizar configuração de rede, "
            "Wi-Fi, roteadores e infraestrutura de conexão."
        )

    elif normalized_language.startswith("en"):
        response = (
            "We can configure networks, "
            "Wi-Fi, routers, and network infrastructure."
        )

    else:
        response = (
            "Podemos realizar configuración de red, "
            "Wi-Fi, routers e infraestructura de conexión."
        )

    return {
        "success": True,
        "workflow": "network_support",
        "response": response,
        "metadata": {
            "company_id": company_id,
            "customer_id": customer_id,
            "service_id": service_id,
            "intent": intent,
            "language": language or "es",
        },
    }
