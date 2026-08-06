"""
Bitey Decision Engine V12

Central business reasoning layer.

Responsibilities:
- Resolve customer intent
- Resolve service
- Route sales
- Route support workflows
- Return execution plan

Does NOT:
- Create tickets
- Save messages
- Send notifications

Those belong to Bitey Core.
"""


from typing import Dict, Any


from app.services.service_resolver import (
    resolve_service
)


from app.services.workflows.workflow_service import (
    execute_workflow
)


from app.services.sales_engine import (
    generate_sales_response
)



# =====================================================
# INTENT GROUPS
# =====================================================


SALES_INTENTS = {

    "ai_assistant",
    "sales",
    "quote",
    "purchase"

}



SUPPORT_INTENTS = {

    "computer_repair",

    "hardware_upgrade",

    "upgrade_hardware",

    "windows_installation",

    "mobile_repair",

    "cctv_installation",

    "camera_installation",

    "network_configuration",

    "software_problem"

}



# =====================================================
# MAIN ENGINE
# =====================================================


def make_decision(
    company_id: int,
    customer: Dict,
    message: str,
    intent: Dict,
    knowledge=None,
    memory=None,
    channel="unknown"
):


    try:


        # ================================
        # SAFETY NORMALIZATION
        # ================================


        if customer is None:

            customer = {}



        if memory is None:

            memory = {}



        if not isinstance(memory, dict):

            memory = {

                "summary": memory

            }



        if intent is None:

            intent = {}



        intent_name = intent.get(
            "intent"
        )


        confidence = intent.get(
            "confidence",
            0
        )



        # ================================
        # SERVICE RESOLUTION
        # ================================


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


            "channel":
                channel


        }



        # =================================================
        # SALES ROUTE
        # =================================================


        if intent_name in SALES_INTENTS:


            customer_name = customer.get(

                "full_name",

                "Cliente"

            )



            response = generate_sales_response(

                intent_name,

                customer_name,

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



                "service":

                    service,



                "service_id":

                    service_id,



                "workflow":

                    None,



                "metadata":

                    metadata


            }



        # =================================================
        # SUPPORT ROUTE
        # =================================================


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



            if workflow is None:

                workflow = {}



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



        # =================================================
        # DEFAULT ROUTE
        # =================================================


        return {


            "action":

                "support",



            "create_ticket":

                True,



            "ticket_type":

                "technical_support",



            "response":

                "Gracias por contactar BiteFixes.",



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



    except Exception as error:


        import traceback


        print(

            "[DECISION ENGINE ERROR]",

            repr(error)

        )


        traceback.print_exc()



        return {


            "action":

                "error",



            "create_ticket":

                False,



            "ticket_type":

                None,



            "response":

                "Error procesando solicitud.",



            "workflow":

                None,



            "ticket":

                None,



            "service":

                None,



            "service_id":

                None,


            "metadata":

                {}

        }




# =====================================================
# COMPATIBILITY WRAPPER
# =====================================================


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