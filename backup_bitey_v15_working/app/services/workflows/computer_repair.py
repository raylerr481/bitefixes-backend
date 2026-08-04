"""
Bitey Computer Repair Workflow V13

Handles:
- Desktop repair
- Notebook repair
- Hardware failures
- Diagnostics

Does NOT:
- create tickets
- save messages
- notify admins
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
            "Podemos realizar diagnóstico e reparo "
            "do computador ou notebook."
        )


        return {

            "success": True,

            "workflow":
                "computer_repair",

            "requires_ticket":
                True,

            "priority":
                "normal",

            "response":
                response,

            "metadata":
            {

                "company_id":
                    company_id,

                "customer_id":
                    customer_id,

                "category":
                    "computer_repair"

            }

        }


    except Exception as error:


        return {

            "success": False,

            "workflow":
                "computer_repair",

            "response":
                "Erro no workflow de reparo.",

            "error":
                str(error)

        }