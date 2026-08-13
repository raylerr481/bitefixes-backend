"""
BiteFixes Decision Engine V12

Central business reasoning layer.

Responsibilities:
- Resolve customer intent
- Resolve service
- Route sales
- Route workflows
- Decide ticket creation
- Decide quote creation
- Return execution plan

Does NOT:
- Create tickets
- Create quotes
- Notify admins
- Save messages

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
# SALES INTENTS
# =====================================================

SALES_INTENTS = {

    "ai_assistant",

    "sales",

    "quote",

    "purchase"

}



# =====================================================
# SUPPORT INTENTS
# =====================================================

SUPPORT_INTENTS = {

    "computer_repair",

    "hardware_upgrade",

    "windows_installation",

    "mobile_repair",

    "cctv_installation",

    "camera_installation",

    "network_configuration",

    "software_problem"

}



# =====================================================
# QUOTE REQUIRED INTENTS
# =====================================================

QUOTE_INTENTS = {

    "ai_assistant",

    "sales",

    "quote",

    "purchase",

    "cctv_installation",

    "camera_installation",

    "network_configuration",

    "hardware_upgrade"

}



# =====================================================
# MAIN DECISION ENGINE
# =====================================================

def make_decision(
    company_id: int,
    customer: Dict,
    message: str,
    intent: Dict,
    knowledge=None,
    memory=None,
    language=None,
    channel="unknown"
):

    intent_name = None

    confidence = 0



    if intent:

        intent_name = intent.get(
            "intent"
        )


        confidence = intent.get(
            "confidence",
            0
        )



    # -------------------------------------
    # Resolve Service
    # -------------------------------------

    service = resolve_service(

        company_id,

        intent_name

    )



    service_id = (

        service.get("id")

        if service

        else None

    )



    requires_quote = (

        intent_name in QUOTE_INTENTS

    )



    metadata = {


        "intent":
            intent_name,


        "confidence":
            confidence,


        "requires_quote":
            requires_quote


    }



    print(

        "[DECISION ENGINE]",

        {

            "intent":
                intent_name,


            "confidence":
                confidence,


            "service_id":
                service_id,


            "requires_quote":
                requires_quote

        }

    )



    # =================================================
    # SALES ROUTE
    # =================================================

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


            "requires_quote":
                requires_quote,


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
            service_id=service_id,
            message=message,

            knowledge=knowledge,
            language=language,
            intent_data=intent

        )



        return {


            "action":
                "workflow",


            "create_ticket":
                True,


            "requires_quote":
                requires_quote,


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


        "requires_quote":
            requires_quote,


        "ticket_type":
            "support",


        "response":

            "Gracias por contactar BiteFixes.",



        "workflow":
            None,


        "service":
            service,


        "service_id":
            service_id,


        "metadata":
            metadata

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
    memory=None,
    language=None
):


    return make_decision(

        company_id,

        customer,

        message,

        intent,

        knowledge,

        memory,

        language

    )









