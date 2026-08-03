"""
Bitey Workflow Router V11

Central workflow dispatcher.

Flow:

Intent
   |
   v
Workflow Router
   |
   v
Specialized Business Workflow
   |
   v
Business Result
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


    try:


        workflow = WORKFLOW_MAP.get(
            intent
        )



        # =============================
        # DEFAULT WORKFLOW
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



        # =============================
        # SELECTED WORKFLOW
        # =============================

        print(

            "[WORKFLOW ROUTER]",

            {
                "intent": intent,

                "workflow":
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


        """
        Compatibility mode.

        Some old workflows do not have
        customer_id parameter.
        """


        print(

            "[WORKFLOW COMPATIBILITY]",

            str(error)

        )


        try:


            return workflow(

                company_id=company_id,

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


                "success":False,


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


            "success":False,


            "response":
                "No fue posible ejecutar el proceso.",


            "error":
                str(error)

        }