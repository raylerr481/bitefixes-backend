"""
BiteFixes Decision Engine

Responsible for:
- Bitey decision routing
- Ticket execution
- Sales/support decisions
"""

from app.services.ticket_service import create_ticket



def decision_engine(
    company_id,
    customer,
    message,
    intent,
    knowledge=None,
    memory=None
):

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


    service_map = {

        "ai_assistant": 16,

        "computer_repair": 1,

        "hardware_upgrade": 7,

        "mobile_repair": 8,

        "camera_installation": 9,

        "network_support": 10

    }


    service_id = service_map.get(
        intent_name
    )


    print(
        "[DECISION ENGINE]",
        {
            "intent": intent_name,
            "confidence": confidence,
            "service_id": service_id
        }
    )


    if intent_name == "ai_assistant":


        return {

            "action": "sales",

            "response":
            """
Perfecto Rayler.

Podemos crear un asistente IA personalizado para tu empresa.

El Bitey AI Assistant puede:

✅ Atender clientes automáticamente por WhatsApp

✅ Responder preguntas frecuentes

✅ Organizar solicitudes y soporte

✅ Automatizar procesos internos

Vamos a preparar una solución adecuada para tu negocio.
""",

            "service_id": service_id,

            "ticket": None,

            "metadata":
            {
                "intent": intent_name,
                "confidence": confidence
            }

        }



    return {

        "action": "fallback",

        "response":
            "Gracias por contactar BiteFixes. Vamos a revisar tu solicitud.",

        "service_id": service_id,

        "ticket": None,

        "metadata":
        {
            "intent": intent_name,
            "confidence": confidence
        }

    }





def execute_decision(
    decision: dict,
    customer_id: int,
    service: dict = None,
    intent: str = None,
    message: str = "",
    company_id: int = 1,
    channel: str = "website"
):

    result = {

        "ticket_id": None,

        "action":
            decision.get("action"),

        "executed": True

    }


    if decision.get("create_ticket") and service:


        ticket = create_ticket(

            customer_id=customer_id,

            service_id=service.get("id"),

            description=message,

            title=service.get("name"),

            intent=intent,

            company_id=company_id,

            channel=channel

        )


        if ticket:

            result["ticket_id"] = ticket.get("id")


    if decision.get("human_required"):

        result["human_required"] = True


    return result