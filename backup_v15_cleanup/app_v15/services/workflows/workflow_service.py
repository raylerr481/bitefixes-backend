"""
Bitey Workflow Router V13

Central workflow dispatcher.

Flow:

Customer Intent
        |
        v
Workflow Router
        |
        v
Specialized Workflow
        |
        v
Business Result

Does NOT:
- create tickets
- save messages
- notifications

Those belong to Bitey Core.
"""


from typing import Dict, Any, Callable

from app.services.workflows import (
    computer_repair,
    hardware_upgrade,
    mobile_repair,
    camera_installation,
    network_support,
    default
)



# =====================================
# WORKFLOW REGISTRY
# =====================================

WORKFLOW_MAP: Dict[str, Callable] = {


    "computer_repair":
        computer_repair.execute,


    "hardware_upgrade":
        hardware_upgrade.execute,


    "mobile_repair":
        mobile_repair.execute,


    "cctv_installation":
        camera_installation.execute,


    "camera_installation":
        camera_installation.execute,


    "network_configuration":
        network_support.execute,


}



# =====================================
# EXECUTOR
# =====================================

def execute_workflow(
    intent: str,
    company_id: int,
    customer_id: int,
    message: str,
    knowledge: Dict[str, Any] | None = None,
    intent_data: Dict[str, Any] | None = None
):


    workflow = None


    try:


        workflow = WORKFLOW_MAP.get(
            intent
        )


        # =============================
        # DEFAULT ROUTE
        # =============================

        if not workflow:


            print(
                "[WORKFLOW ROUTER]",
                "default"
            )


            return default.execute(

                company_id=company_id,

                customer_id=customer_id,

                message=message,

                knowledge=knowledge,

                intent=intent_data

            )



        print(

            "[WORKFLOW ROUTER]",

            {

                "intent": intent,

                "module":
                    workflow.__module__

            }

        )



        result = workflow(

            company_id=company_id,

            customer_id=customer_id,

            message=message,

            knowledge=knowledge,

            intent=intent_data

        )


        return result



    except TypeError as error:


        print(

            "[WORKFLOW COMPATIBILITY]",

            str(error)

        )


        # Legacy workflows compatibility

        try:


            if workflow:


                return workflow(

                    company_id=company_id,

                    message=message,

                    knowledge=knowledge,

                    intent=intent_data

                )


            return default.execute(

                company_id=company_id,

                customer_id=customer_id,

                message=message,

                knowledge=knowledge,

                intent=intent_data

            )



        except Exception as fallback_error:


            print(

                "[WORKFLOW FALLBACK ERROR]",

                repr(fallback_error)

            )


            return {


                "success": False,


                "response":
                    "Workflow unavailable.",


                "error":
                    str(fallback_error)

            }



    except Exception as error:


        print(

            "[WORKFLOW ROUTER ERROR]",

            repr(error)

        )


        return {


            "success": False,


            "workflow":
                intent,


            "response":
                "No fue posible ejecutar el proceso.",


            "error":
                str(error)

        }