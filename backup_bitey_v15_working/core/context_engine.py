"""
BiteFixes Context Engine V6

Builds Bitey intelligence context.

Responsibilities:
- Memory
- Customer profile
- Statistics
- Service recommendations
- Product recommendations
- Conversation stage
- AI preparation
"""

from app.services.chat_memory import (
    build_memory_context,
    get_memory_state
)

from app.services.learning_service import (
    get_customer_profile,
    get_customer_statistics,
    get_recommended_services,
    get_services_by_intent
)

from app.services.product_service import (
    get_available_products
)

from app.services.ia_engine import (
    prepare_conversation_context
)


def build_context(
    customer_id: int,
    message: str,
    intent=None,
    company_id=1
):

    # =====================
    # MEMORY
    # =====================

    memory = build_memory_context(
        customer_id
    )


    memory_state = get_memory_state(
        customer_id
    )


    # =====================
    # PROFILE
    # =====================

    profile = get_customer_profile(
        customer_id
    )


    statistics = get_customer_statistics(
        customer_id
    )


    # =====================
    # RECOMMENDATIONS
    # =====================

    service_recommendations = []

    product_recommendations = []


    # Current intent has priority

    if intent == "buy_product":

        product_recommendations = (
            get_available_products(
                company_id
            )
        )


    elif intent:

        service_recommendations = (
            get_services_by_intent(
                intent,
                company_id
            )
        )


    else:

        service_recommendations = (
            get_recommended_services(
                customer_id
            )
        )


    # =====================
    # CONVERSATION STAGE
    # =====================

    conversation_stage = (
        memory_state.get(
            "conversation_stage"
        )
    )


    # =====================
    # AI CONTEXT
    # =====================

    ai_context = prepare_conversation_context(

        message,

        memory,

        memory_state

    )


    # =====================
    # FINAL CONTEXT
    # =====================

    return {

        "customer_id":
            customer_id,


        "current_message":
            message,


        "current_intent":
            intent,


        "memory":
            memory,


        "memory_size":
            len(memory),


        "memory_state":
            memory_state,


        "conversation_stage":
            conversation_stage,


        "profile":
            profile,


        "statistics":
            statistics,


        "service_recommendations":
            service_recommendations,


        "product_recommendations":
            product_recommendations,


        "ai_context":
            ai_context

    }