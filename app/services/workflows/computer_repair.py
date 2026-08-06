"""
Bitey Workflow
Computer Repair
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
            "computer_repair",

        "response":
            "Vamos a revisar tu equipo y realizar "
            "el diagnóstico técnico correspondiente.",

        "metadata": {

            "company_id": company_id,
            "customer_id": customer_id,
            "service_id": service_id,
            "intent": intent,
            "language": language

        }

    }