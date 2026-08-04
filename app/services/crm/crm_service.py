"""
=====================================================
BiteFixes CRM Service V16
=====================================================

Responsibilities

- CRM orchestration
- Update customer status
- Update pipeline
- Create leads
- Build customer profile
- Prepare future automations

=====================================================
"""

from typing import Optional

from app.services.crm.pipeline_service import update_pipeline
from app.services.crm.lead_service import create_or_update_lead
from app.services.crm.customer_profile import update_customer_profile


def process_crm(
    customer_id: int,
    ticket: Optional[dict],
    service: Optional[dict],
    intent: Optional[str],
    language: str,
    response: str
):
    """
    Main CRM entry point.
    Called after workflow execution.
    """

    try:

        print("[CRM] Processing customer", customer_id)

        ticket_id = None
        service_id = None

        if ticket:
            ticket_id = ticket.get("id")

        if service:
            service_id = service.get("id")

        # ------------------------------------------
        # Update Lead
        # ------------------------------------------

        lead = create_or_update_lead(

            customer_id=customer_id,

            service_id=service_id,

            ticket_id=ticket_id,

            intent=intent

        )

        # ------------------------------------------
        # Update Pipeline
        # ------------------------------------------

        pipeline = update_pipeline(

            customer_id=customer_id,

            ticket=ticket,

            service=service,

            intent=intent

        )

        # ------------------------------------------
        # Update Customer Profile
        # ------------------------------------------

        profile = update_customer_profile(

            customer_id=customer_id,

            language=language,

            last_ticket=ticket,

            last_service=service,

            last_intent=intent

        )

        print("[CRM] OK")

        return {

            "success": True,

            "lead": lead,

            "pipeline": pipeline,

            "profile": profile

        }

    except Exception as error:

        print("[CRM ERROR]", error)

        return {

            "success": False,

            "error": str(error)

        }