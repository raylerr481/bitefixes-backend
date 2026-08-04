"""
Bitey Decision Engine V12

Central business reasoning layer.

Responsibilities:
- Resolve customer intent
- Resolve service
- Route sales
- Route technical workflows
- Return execution plan

Does NOT:
- create tickets
- save messages
- notify admins

Those belong to Bitey Core.
"""


from typing import Dict, Any

from app.services.service_resolver import resolve_service
from app.services.sales_engine import generate_sales_response
from app.services.workflows.workflow_service import execute_workflow



SALES_INTENTS = {

    "ai_assistant",
    "sales",
    "quote",
    "purchase",

}



SUPPORT_INTENTS = {

    "computer_repair",

    "hardware_upgrade",

    "windows_installation",

    "mobile_repair",

    "cctv_installation",

    "camera_installation",

    "network_configuration",

    "software_problem",

}



def make_decision(
    company_id: int,
    customer: Dict,
    message: str,
    intent: Dict,
    knowledge=None,
    memory=None,
    channel="unknown",
):

    """
    Main Bitey reasoning engine.
    Returns execution plan.
    """


    try:


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



        service = resolve_service(

            company_id,

            intent_name

        )



        service_id = None


        if service:

            service_id = service.get(
                "id"
            )



        print(

            "[DECISION ENGINE]",

            {

                "intent":
                    intent_name,

                "confidence":
                    confidence,

                "service_id":
                    service_id

            }

        )



        metadata = {

            "intent":
                intent_name,

            "confidence":
                confidence,

        }



        # =====================================
        # SALES ROUTE
        # =====================================


        if intent_name in SALES_INTENTS:


            response = generate_sales_response(

                intent_name,

                customer.get(
                    "full_name",
                    "Cliente"
                ),

                memory

            )


            return {


                "action":
                    "sales",


                "create_ticket":
                    True,


                "ticket_type":
                    "sales",


                "response":
                    response,


                "workflow":
                    None,


                "ticket":
                    None,


                "service":
                    service,


                "service_id":
                    service_id,


                "metadata":
                    metadata

            }




        # =====================================
        # TECHNICAL ROUTE
        # =====================================


        if intent_name in SUPPORT_INTENTS:



            workflow = execute_workflow(

                intent=intent_name,

                company_id=company_id,

                customer_id=customer.get(
                    "id"
                ),

                message=message,

                knowledge=knowledge,

                intent_data=intent

            )



            return {


                "action":
                    "workflow",


                "create_ticket":
                    True,


                "ticket_type":
                    "technical_support",


                "response":
                    workflow.get(

                        "response",

                        "Solicitud recibida."

                    ),


                "workflow":
                    intent_name,


                "ticket":
                    workflow.get(
                        "ticket"
                    ),


                "service":
                    service,


                "service_id":
                    service_id,


                "metadata":
                    metadata

            }





        # =====================================
        # DEFAULT
        # =====================================


        return {


            "action":
                "support",


            "create_ticket":
                True,


            "ticket_type":
                "support",


            "response":
                "Gracias por contactar BiteFixes. Vamos a revisar tu solicitud.",


            "workflow":
                "default",


            "ticket":
                None,


            "service":
                service,


            "service_id":
                service_id,


            "metadata":
                metadata

        }




    except Exception as error:


        print(

            "[DECISION ENGINE ERROR]",

            repr(error)

        )


        return {


            "action":
                "error",


            "create_ticket":
                False,


            "response":
                "Error procesando solicitud.",


            "workflow":
                None,


            "ticket":
                None,


            "service":
                None,


            "service_id":
                None

        }





# ==========================================
# Compatibility wrapper
# ==========================================


def decision_engine(
    company_id:int,
    customer:dict,
    message:str,
    intent:dict,
    knowledge=None,
    memory=None,
):


    return make_decision(

        company_id,

        customer,

        message,

        intent,

        knowledge,

        memory

    )