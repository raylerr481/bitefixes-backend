"""
Bitey Hardware Upgrade Workflow V13

Handles:
- SSD upgrade
- RAM upgrade
- Notebook performance

Returns execution plan only.

Does NOT:
- create ticket
- save messages
- notifications
"""


def execute(
    company_id: int,
    customer_id: int,
    message: str,
    knowledge=None,
    intent=None
):

    try:

        response = (
            "Podemos melhorar o desempenho do notebook "
            "com upgrade de SSD e memória RAM."
        )


        return {

            "success": True,

            "workflow":
                "hardware_upgrade",

            "requires_ticket":
                True,

            "priority":
                "normal",

            "response":
                response,

            "metadata":
            {
                "company_id": company_id,
                "customer_id": customer_id,
                "service":
                    "Notebook upgrade SSD and RAM"
            }

        }


    except Exception as error:


        return {

            "success": False,

            "workflow":
                "hardware_upgrade",

            "response":
                "Erro no workflow de hardware.",

            "error":
                str(error)

        }