"""
BiteFixes Sales Engine V2

Commercial intelligence layer.

Responsibilities:
- Detect business context
- Read customer memory
- Generate contextual sales conversations
- Support AI Assistant sales flow
"""


def has_business_context(memory):
    """
    Detect if customer already provided business information.
    """

    if not memory:
        return False


    keywords = [
        "empresa",
        "negocio",
        "tienda",
        "clientes",
        "whatsapp",
        "ventas",
        "soporte",
        "servicio",
        "local"
    ]


    for item in memory:

        content = item.get(
            "content",
            ""
        ).lower()


        for keyword in keywords:

            if keyword in content:
                return True


    return False



def extract_business_context(memory):
    """
    Extract customer information from memory.
    """

    if not memory:
        return ""


    result = []


    for item in memory:

        if item.get("role") == "customer":

            result.append(
                item.get(
                    "content",
                    ""
                )
            )


    return " ".join(result)



def generate_ai_assistant_response(
    customer_name,
    memory=None
):
    """
    Generate AI Assistant commercial response.
    """


    business_detected = has_business_context(
        memory
    )


    if business_detected:


        context = extract_business_context(
            memory
        )


        return f"""
Perfecto {customer_name}.

Entendi que sua empresa precisa de um assistente IA.

Informações identificadas:

{context}


O Bitey AI Assistant pode ajudar sua empresa com:

✅ Atendimento automático pelo WhatsApp

✅ Respostas inteligentes para clientes

✅ Criação automática de tickets

✅ Organização de pedidos e serviços

✅ Acompanhamento de clientes


Para montar uma solução adequada:

1. Quantos clientes sua empresa atende por mês?

2. Você utiliza WhatsApp Business atualmente?

3. Deseja automatizar vendas e suporte?
"""


    return f"""
Perfeito {customer_name}.

Podemos criar um assistente IA personalizado para sua empresa.

O Bitey AI Assistant ajuda empresas a:

✅ atender clientes automaticamente

✅ responder perguntas frequentes

✅ organizar suporte

✅ automatizar processos internos


Para recomendar a melhor solução:

Qual é o tipo da sua empresa e quais processos deseja automatizar?
"""



def generate_sales_response(
    intent,
    customer_name,
    memory=None
):
    """
    Main commercial router.
    """


    if intent == "ai_assistant":

        return generate_ai_assistant_response(
            customer_name,
            memory
        )


    return (
        "Obrigado pelo contato. "
        "Um especialista irá ajudar você."
    )