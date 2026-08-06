"""
Bitey Workflow Router V18
Central workflow executor
"""


import importlib



WORKFLOW_MAP = {

    "cctv_installation":
        "app.services.workflows.camera_installation",

    "windows_installation":
        "app.services.workflows.windows_installation",

    "hardware_upgrade":
        "app.services.workflows.hardware_upgrade",

    "computer_repair":
        "app.services.workflows.computer_repair"

}



def execute_workflow(
    intent,
    message,
    company_id=None,
    customer_id=None,
    service_id=None,
    customer=None,
    language=None,
    knowledge=None,
    **kwargs
):


    module_path = WORKFLOW_MAP.get(intent)


    if not module_path:

        return {

            "success": False,

            "workflow": None,

            "response":
                "No workflow configured."

        }



    try:

        module = importlib.import_module(module_path)



        result = module.execute(

            message=message,

            company_id=company_id,

            customer_id=customer_id,

            service_id=service_id,

            intent=intent,

            customer=customer,

            language=language

        )


        return result



    except Exception as e:


        print("[WORKFLOW EXECUTION ERROR]", repr(e))


        return {

            "success": False,

            "workflow": intent,

            "response":
                "Workflow execution failed.",

            "error":
                str(e)

        }