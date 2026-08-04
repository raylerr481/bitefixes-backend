"""
BiteFixes Response Engine V5

Generates human friendly Bitey responses.

Responsibilities:

- Product sales
- Service sales
- Technical support
- Knowledge answers
- Ticket communication
"""


def format_product(product):

    text = []

    text.append(
        f"💻 {product.get('name')}"
    )


    if product.get("brand"):

        text.append(
            f"Marca: {product.get('brand')}"
        )


    if product.get("model"):

        text.append(
            f"Modelo: {product.get('model')}"
        )


    if product.get("ram"):

        text.append(
            f"RAM: {product.get('ram')}"
        )


    if product.get("storage"):

        text.append(
            f"SSD/HDD: {product.get('storage')}"
        )


    if product.get("processor"):

        text.append(
            f"Procesador: {product.get('processor')}"
        )


    if product.get("price"):

        text.append(
            f"Precio: R$ {product.get('price')}"
        )


    return "\n".join(text)



def generate_response(

    intent=None,

    service=None,

    knowledge=None,

    ticket_id=None,

    customer_name="Cliente",

    decision=None,

    context=None

):


    decision = decision or {}



    # =====================
    # PRODUCT SALES
    # =====================


    if decision.get(
        "use_products"
    ):


        products = []


        if context:

            products = context.get(
                "product_recommendations",
                []
            )


        if products:


            response = (

                "Encontré estos equipos disponibles:\n\n"

            )


            for product in products[:3]:


                response += (

                    format_product(product)

                    +

                    "\n\n"

                )


            response += (

                "¿Quieres más detalles o fotos?"

            )


            return response



        return (

            "Cuéntame tu presupuesto y el uso "

            "que necesitas para recomendarte un equipo."

        )



    # =====================
    # AI ASSISTANT SALES
    # =====================


    if intent == "ai_assistant":


        response = (

            f"Perfecto {customer_name}.\n\n"

            "Podemos ayudarte a implementar "

            "un asistente IA personalizado "

            "para tu empresa.\n\n"

            "Nuestro servicio AI Assistant permite "

            "automatizar atención al cliente, "

            "WhatsApp y procesos internos utilizando "

            "inteligencia artificial.\n\n"

            "Para recomendarte la mejor solución: "

            "¿qué tipo de empresa tienes y qué "

            "procesos quieres automatizar?"

        )


        return response



    # =====================
    # OTHER SALES SERVICES
    # =====================


    if (

        service

        and

        decision.get("workflow")

        ==

        "sales"

    ):


        return (

            f"Perfecto {customer_name}.\n\n"

            f"Podemos ayudarte con "

            f"{service.get('name')}.\n\n"

            f"{service.get('description','')}\n\n"

            "Cuéntame más sobre tu necesidad "

            "para preparar una solución adecuada."

        )



    # =====================
    # TECHNICAL SUPPORT
    # =====================


    if service:


        response = (

            f"Podemos ayudarte con "

            f"{service.get('name')}.\n\n"

        )


        description = service.get(
            "description"
        )


        if description:


            response += (

                description

                +

                "\n"

            )


        if ticket_id:


            response += (

                f"\nTicket asociado: #{ticket_id}"

            )


        return response



    # =====================
    # KNOWLEDGE BASE
    # =====================


    if knowledge:


        if isinstance(

            knowledge,

            dict

        ):


            answer = knowledge.get(
                "answer"
            )


            if answer:

                return answer



    # =====================
    # DEFAULT
    # =====================


    return (

        f"Hola {customer_name}. "

        "¿Cómo puedo ayudarte?"

    )