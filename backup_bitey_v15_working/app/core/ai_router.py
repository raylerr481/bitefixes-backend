"""
BiteFixes Context Engine

Builds a unified context object for Bitey AI.

Responsibilities
----------------
- Customer profile
- Conversation
- Chat memory
- Previous intent
- Learning profile
- Statistics
- Recommended services
- Current message analysis
"""

from app.services.chat_memory import (
    build_memory_context,
    get_last_intent
)

from app.services.learning_service import (
    get_customer_profile,
    get_customer_statistics,
    get_recommended_services
)

from app.services.ia_engine import (
    prepare_conversation_context
)


def build_context(
    customer_id: int,
    message: str
):
    """
    Build the complete AI context.
    """

    memory = build_memory_context(customer_id)

    previous_intent = get_last_intent(
        customer_id
    )

    profile = get_customer_profile(
        customer_id
    )

    statistics = get_customer_statistics(
        customer_id
    )

    recommendations = (
        get_recommended_services(
            customer_id
        )
    )

    ai_context = (
        prepare_conversation_context(
            message,
            memory,
            previous_intent
        )
    )

    return {

        "customer_id": customer_id,

        "message": message,

        "memory": memory,

        "memory_size": len(memory),

        "previous_intent": previous_intent,

        "profile": profile,

        "statistics": statistics,

        "recommendations": recommendations,

        "ai_context": ai_context

    }