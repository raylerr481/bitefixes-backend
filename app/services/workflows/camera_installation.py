"""
BiteFixes Workflow
CCTV Installation
Multilingual ES / PT / EN
"""

def execute(
    message=None,
    company_id=None,
    customer_id=None,
    conversation_id=None,
    service_id=None,
    intent=None,
    knowledge=None,
    customer=None,
    language=None,
    **kwargs
):
    normalized_language = (language or "es").lower()

    if normalized_language.startswith("pt"):
        response = (
            "Realizamos instalação de câmeras de segurança, "
            "configuração de DVR/NVR, ajustes de rede "
            "e acesso remoto para monitoramento."
        )

    elif normalized_language.startswith("en"):
        response = (
            "We perform security camera installation, "
            "DVR/NVR configuration, network adjustments "
            "and remote monitoring setup."
        )

    else:
        response = (
            "Realizamos instalación de cámaras de seguridad, "
            "configuración de DVR/NVR, ajustes de red "
            "y acceso remoto para monitoreo."
        )

    return {
        "success": True,
        "workflow": "cctv_installation",
        "response": response,
        "service_id": service_id,
        "intent": intent,
        "metadata": {
            "company_id": company_id,
            "customer_id": customer_id,
            "conversation_id": conversation_id,
            "service_id": service_id,
            "intent": intent,
            "language": language or "es",
            "workflow": "cctv_installation",
        },
    }
