"""
Bitey Decision Engine V13

Business reasoning layer.

Responsibilities:

- Resolve intent
- Resolve service
- Decide sales/support/knowledge
- Prepare execution plan

Does NOT:
- Create tickets
- Save messages
- Notify

"""


from typing import Dict


from app.services.service_resolver import (
    resolve_service
)


from app.services.workflows.workflow_service import (
    execute_workflow
)


from app.services.sales_engine import (
    generate_sales_response
)



SALES_INTENTS = {

    "ai_assistant",

    "quote",

    "purchase",

    "sales",

    "cctv_installation",

    "camera_installation"

}



SUPPORT_INTENTS = {


    "computer_repair",

    "hardware_upgrade",

    "upgrade_hardware",

    "windows_installation",

    "mobile_repair",

    "network_configuration",

    "software_problem"

}




def make_decision(
    company_id:int,
    customer:Dict,
    message:str,
    intent:Dict,
    knowledge=None,
    memory=None,
    channel="unknown"
):


    try:


        customer = customer or {}

        memory = memory or {}

        intent = intent or {}



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



        metadata={


            "intent":
                intent_name,


            "confidence":
                confidence,


            "channel":
                channel


        }




        print(
            "[DECISION]",
            {
                "intent":intent_name,
                "service_id":service_id
            }
        )



        # =====================================
        # KNOWLEDGE WITHOUT ACTION
        # =====================================


        if (

            knowledge

            and

            not intent_name

        ):


            return {


                "action":
                    "knowledge",


                "create_ticket":
                    False,


                "ticket_type":
                    None,


                "response":
                    knowledge,


                "service":
                    service,


                "service_id":
                    service_id,


                "metadata":
                    metadata

            }




        # =====================================
        # SALES
        # =====================================


        if intent_name in SALES_INTENTS:



            sales = generate_sales_response(

                intent_name,

                message,

                memory,

                knowledge

            )



            return {


                "action":
                    "sales",


                "create_ticket":
                    True,


                "requires_quote":
                    True,


                "ticket_type":
                    "sales",


                "response":
                    sales,


                "service":
                    service,


                "service_id":
                    service_id,


                "metadata":
                    metadata


            }





        # =====================================
        # SUPPORT
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


            workflow = workflow or {}



            return {


                "action":
                    "workflow",


                "create_ticket":
                    True,


                "requires_quote":
                    False,


                "ticket_type":
                    "technical_support",


                "response":
                    workflow.get(

                        "response",

                        "Solicitud recibida."

                    ),


                "workflow":
                    intent_name,


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
                "technical_support",


            "requires_quote":
                False,


            "response":
                "Gracias por contactar BiteFixes.",


            "service":
                service,


            "service_id":
                service_id,


            "metadata":
                metadata

        }




    except Exception as error:


        import traceback


        traceback.print_exc()



        return {


            "action":
                "error",


            "create_ticket":
                False,


            "response":
                "Error procesando solicitud.",


            "service":
                None,


            "service_id":
                None

        }




def decision_engine(
    company_id,
    customer,
    message,
    intent,
    knowledge=None,
    memory=None,
    channel="unknown"
):


    return make_decision(

        company_id,

        customer,

        message,

        intent,

        knowledge,

        memory,

        channel

    )