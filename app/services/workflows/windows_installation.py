"""
Bitey Workflow
Hardware Upgrade
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

    return {

        "success": True,

        "workflow":
            "hardware_upgrade",

        "response":
            "Realizamos actualización de hardware, "
            "instalación de SSD, ampliación de memoria RAM "
            "y mejoras de rendimiento.",

        "metadata": {

            "company_id": company_id,
            "customer_id": customer_id,
            "service_id": service_id,
            "intent": intent,
            "language": language

        }

    }