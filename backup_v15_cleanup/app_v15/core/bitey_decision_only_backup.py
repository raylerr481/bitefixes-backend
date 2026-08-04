"""
Bitey Decision Engine V6

Central reasoning layer.

Responsibilities:
- Analyze intent
- Resolve service
- Route sales workflows
- Route support workflows
- Generate final decision
"""

from typing import Dict, Any

from app.services.workflows.workflow_service import execute_workflow
from app.services.sales_engine import generate_sales_response


SERVICE_MAP = {

    "ai_assistant": 16,

    "computer_repair": 1,

    "hardware_upgrade": 7,

    "mobile_repair": 8,

    "camera_installation": 9,

    "network_support": 10,

}


SALES_INTENTS = {

    "ai_assistant",

    "sales",

    "quote",

    "purchase",

}


SUPPORT_INTENTS = {

    "computer_repair",

    "hardware_upgrade",

    "mobile_repair",

    "camera_installation",

    "network_support",

    "software_problem",

}



def normalize_customer(customer):

    """
    Converts customer data into a safe format.
    """

    if isinstance(customer, dict):

        return customer


    if isinstance(customer, str):

        return {

            "full_name": customer

        }


    return {

        "full_name": "Cliente"

    }



def make_decision(
    company_id: int,
    customer,
    message: str,
    intent: dict,
    knowledge=None,
    memory=None
):

    try:

        customer = normalize_customer(customer)


        intent_name = None

        confidence = 0



        if isinstance(intent, dict):

            intent_name = intent.get(
                "intent"
            )

            confidence = intent.get(
                "confidence",
                0
            )



        service_id = SERVICE_MAP.get(
            intent_name
        )



        print(
            "[DECISION]",
            {
                "intent": intent_name,
                "confidence": confidence,
                "service_id": service_id
            }
        )



        customer_name = customer.get(
            "full_name",
            "Cliente"
        )



        #
        # SALES FLOW
        #

        if intent_name in SALES_INTENTS:


            sales_context = {

                "message": message,

                "customer": customer,

                "memory": memory,

                "knowledge": knowledge

            }



            response = generate_sales_response(

                intent_name,

                customer_name,

                sales_context

            )



            return {

                "action": "sales",

                "response": response,

                "workflow": None,

                "ticket": None,

                "service_id": service_id,

                "metadata": {

                    "intent": intent_name,

                    "confidence": confidence

                }

            }




        #
        # SUPPORT FLOW
        #

        if intent_name in SUPPORT_INTENTS:


            workflow = execute_workflow(

                intent_name,

                company_id,

                message,

                knowledge,

                intent

            )



            return {

                "action": "workflow",

                "response": workflow.get(

                    "response",

                    "Solicitud recibida."

                ),

                "workflow": intent_name,

                "ticket": workflow.get(

                    "ticket"

                ),

                "service_id": service_id,

                "metadata": workflow.get(

                    "metadata",

                    {}

                )

            }




        #
        # FALLBACK
        #

        return {

            "action": "fallback",

            "response":

                "Gracias por contactar BiteFixes. Vamos a revisar tu solicitud.",

            "workflow": "default",

            "ticket": None,

            "service_id": service_id,

            "metadata": {

                "intent": intent_name,

                "confidence": confidence

            }

        }



    except Exception as e:


        print(
            "[DECISION ENGINE ERROR]",
            repr(e)
        )


        return {

            "action": "error",

            "response":

                "Ocurrió un error procesando la solicitud.",

            "service_id": None,

            "ticket": None

        }




def decision_engine(
    company_id,
    customer,
    message,
    intent,
    knowledge=None,
    memory=None
):

    return make_decision(

        company_id,

        customer,

        message,

        intent,

        knowledge,

        memory

    )