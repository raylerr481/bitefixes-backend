"""
Bitey Sales Engine V2

Genera respuestas comerciales inteligentes
para servicios, ventas y captación de leads.

Compatible con:
- Supabase
- base_conhecimento
- historial_chats
- AI Assistant
- CRM
"""


def normalize_items(items):

    """
    Convierte cualquier entrada en lista segura.
    """

    if not items:
        return []

    if isinstance(items, list):
        return items

    return [items]



def has_business_context(context):

    """
    Detecta si el cliente habla de empresa/negocio.
    """

    items = normalize_items(context)


    keywords = [
        "empresa",
        "negocio",
        "loja",
        "tienda",
        "cliente",
        "ventas",
        "automatizar",
        "atender",
        "whatsapp",
        "crm"
    ]


    for item in items:


        if isinstance(item, dict):

            content = (
                item.get("content")
                or
                item.get("message_content")
                or
                item.get("texto")
                or
                ""
            )


        else:

            content = str(item)



        content = content.lower()



        for word in keywords:

            if word in content:
                return True



    return False




def generate_ai_assistant_response(
        message,
        customer_context=None,
        knowledge=None
):


    business_detected = has_business_context(
        customer_context
    )


    text = message.lower()



    if business_detected or "empresa" in text:


        return {

            "response":
            (
            "Excelente. Bitey AI puede ayudarte "
            "a automatizar la atención de clientes, "
            "WhatsApp, página web, CRM y procesos "
            "de tu empresa."
            ),

            "intent":
            "ai_assistant",

            "lead":
            True
        }



    return {


        "response":
        (
        "Bitey AI es un asistente inteligente "
        "para empresas que permite automatizar "
        "atención y soporte."
        ),

        "intent":
        "ai_assistant",

        "lead":
        False

    }




def generate_sales_response(
        intent,
        message,
        customer_context=None,
        knowledge=None
):


    if intent == "ai_assistant":


        return generate_ai_assistant_response(
            message,
            customer_context,
            knowledge
        )



    return {


        "response":
        "Gracias por contactarnos. Un especialista revisará tu solicitud.",

        "lead":
        False
    }