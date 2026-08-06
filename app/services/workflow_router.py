"""
BiteFixes Workflow Router
Bitey Core V15

Responsabilidades
-----------------
- Resolver el workflow correspondiente a una intención.
- Ejecutar el workflow.
- Mantener compatibilidad con Bitey Core.
"""

from app.services.workflows.ai_assistant import run as ai_assistant
from app.services.workflows.camera_installation import run as camera_installation
from app.services.workflows.computer_repair import run as computer_repair
from app.services.workflows.hardware_upgrade import run as hardware_upgrade
from app.services.workflows.mobile_repair import run as mobile_repair
from app.services.workflows.network_support import run as network_support
from app.services.workflows.printer_support import run as printer_support
from app.services.workflows.software_support import run as software_support
from app.services.workflows.windows_installation import run as windows_installation
from app.services.workflows.web_support import run as web_support
from app.services.workflows.default import run as default_workflow


WORKFLOWS = {

    "ai_assistant": ai_assistant,

    "computer_repair": computer_repair,

    "hardware_upgrade": hardware_upgrade,

    "upgrade_hardware": hardware_upgrade,

    "windows_installation": windows_installation,

    "mobile_repair": mobile_repair,

    "network_configuration": network_support,

    "printer_support": printer_support,

    "software_problem": software_support,

    "cctv_installation": camera_installation,

    "camera_installation": camera_installation,

    "website": web_support,

}


def execute_workflow(
    intent: str,
    **kwargs
):
    workflow = WORKFLOWS.get(intent)

    if workflow is None:
        workflow = default_workflow

    return workflow(**kwargs)


# Compatibilidad con versiones anteriores
route_workflow = execute_workflow