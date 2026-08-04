"""
BiteFixes Notification Service V14

Responsible for:
- Admin notifications
- Ticket events
- Workflow events
- Bitey AI alerts

Does NOT:
- create tickets
- modify customers
- execute workflows


Table:
admin_notifications

Fields:
id
company_id
customer_id
ticket_id
service_id
message
intent
channel
priority
status
created_at
"""


from datetime import datetime

from app.database.supabase import supabase



# =====================================================
# CREATE NOTIFICATION
# =====================================================


def create_notification(
    company_id: int,
    message: str,
    customer_id: int = None,
    ticket_id: int = None,
    service_id: int = None,
    intent: str = None,
    channel: str = "website",
    priority: str = "medium"
):

    try:


        data = {


            "company_id":
                company_id,


            "customer_id":
                customer_id,


            "ticket_id":
                ticket_id,


            "service_id":
                service_id,


            "message":
                message,


            "intent":
                intent,


            "channel":
                channel,


            "priority":
                priority,


            "status":
                "new",


            "created_at":
                datetime.utcnow().isoformat()

        }



        result = (

            supabase

            .table(
                "admin_notifications"
            )

            .insert(data)

            .execute()

        )



        print(
            "[NOTIFICATION CREATED]",
            result.data
        )



        return result.data



    except Exception as error:


        print(
            "[NOTIFICATION ERROR]",
            error
        )


        return None





# =====================================================
# EVENT ROUTER
# =====================================================


def notify_event(
    company_id: int,
    event: str,
    ticket_id: int = None,
    customer_id: int = None,
    service_id: int = None,
    message: str = None,
    intent: str = None,
    channel: str = "website",
    priority: str = "medium",
    metadata: dict = None
):


    try:


        if message is None:

            message = event



        if metadata:


            message = (
                message
                +
                " | "
                +
                str(metadata)
            )



        return create_notification(

            company_id=company_id,

            message=message,

            customer_id=customer_id,

            ticket_id=ticket_id,

            service_id=service_id,

            intent=intent or event,

            channel=channel,

            priority=priority

        )



    except Exception as error:


        print(
            "[EVENT NOTIFICATION ERROR]",
            error
        )


        return None





# =====================================================
# SHORTCUTS
# =====================================================


def notify_new_ticket(
    company_id,
    ticket_id,
    customer_id,
    service_id,
    intent,
    message
):


    return notify_event(

        company_id,

        event="new_ticket",

        ticket_id=ticket_id,

        customer_id=customer_id,

        service_id=service_id,

        intent=intent,

        message=message

    )




def notify_workflow_started(
    company_id,
    ticket_id,
    customer_id,
    workflow
):


    return notify_event(

        company_id,

        event="workflow_started",

        ticket_id=ticket_id,

        customer_id=customer_id,

        intent=workflow,

        message=
            f"Workflow iniciado: {workflow}"

    )




def notify_customer_request(
    company_id,
    customer_id,
    ticket_id,
    intent,
    message
):


    return notify_event(

        company_id,

        event="customer_request",

        customer_id=customer_id,

        ticket_id=ticket_id,

        intent=intent,

        message=message

    )