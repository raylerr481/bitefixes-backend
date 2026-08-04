"""
BiteFixes IA Engine V4

Conversation preparation layer.

Responsibilities:
- Normalize user message
- Prepare AI context
- Combine memory and state
- Support Bitey reasoning
"""

from app.utils.normalizer import (
    normalizar_texto
)


def prepare_conversation_context(
    message: str,
    memory: list,
    memory_state: dict | None = None
):

    memory_state = memory_state or {}


    normalized_message = normalizar_texto(
        message
    )


    context = {

        "message": message,

        "normalized_message": normalized_message,

        "memory": memory,

        "memory_size": len(memory),

        "memory_state": memory_state,

        "last_intent": memory_state.get(
            "last_intent"
        ),

        "last_sales_intent": memory_state.get(
            "last_sales_intent"
        ),

        "last_support_intent": memory_state.get(
            "last_support_intent"
        ),

        "conversation_stage": memory_state.get(
            "conversation_stage"
        )

    }


    return context



def analyze_conversation_context(
    context: dict
):

    """
    Basic conversational analysis.

    Later this layer can integrate:
    - LLM
    - embeddings
    - sentiment
    - customer behavior
    """


    analysis = {

        "has_history": False,

        "previous_intent": None,

        "conversation_stage": None

    }


    if context.get(
        "memory"
    ):

        analysis["has_history"] = True



    analysis["previous_intent"] = context.get(
        "last_intent"
    )


    analysis["conversation_stage"] = context.get(
        "conversation_stage"
    )


    return analysis