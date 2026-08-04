"""
BiteFixes Chat Memory Service V5

Handles Bitey conversational memory.

Responsibilities:
- Retrieve previous messages
- Build conversation context
- Track last intents
- Track sales/support memory
- Detect conversation stage
"""

from app.database.supabase import database


# =====================================================
# GET CHAT HISTORY
# =====================================================

def get_chat_history(
    customer_id: int,
    limit: int = 10
):

    try:

        result = (
            database
            .table("messages")
            .select("*")
            .eq(
                "customer_id",
                customer_id
            )
            .order(
                "created_at",
                desc=True
            )
            .limit(limit)
            .execute()
        )


        messages = result.data or []


        return list(
            reversed(messages)
        )


    except Exception as error:

        print(
            "[CHAT MEMORY ERROR]",
            error
        )

        return []



# =====================================================
# BUILD MEMORY CONTEXT
# =====================================================

def build_memory_context(
    customer_id: int,
    limit: int = 5
):

    history = get_chat_history(
        customer_id,
        limit
    )


    context = []


    for item in history:

        sender = item.get(
            "sender_type",
            ""
        )


        message = item.get(
            "message_content",
            ""
        )


        context.append(
            {
                "role": sender,
                "content": message
            }
        )


    return context



# =====================================================
# LAST INTENT
# =====================================================

def get_last_intent(
    customer_id:int
):

    try:

        result = (
            database
            .table("messages")
            .select("intent")
            .eq(
                "customer_id",
                customer_id
            )
            .not_.is_(
                "intent",
                "null"
            )
            .order(
                "created_at",
                desc=True
            )
            .limit(1)
            .execute()
        )


        if result.data:

            return result.data[0].get(
                "intent"
            )


        return None


    except Exception as error:

        print(
            "[LAST INTENT ERROR]",
            error
        )

        return None



# =====================================================
# LAST SALES INTENT
# =====================================================

def get_last_sales_intent(
    customer_id:int
):

    sales_intents = [
        "buy_product",
        "software_sales",
        "ai_assistant"
    ]


    history = get_chat_history(
        customer_id,
        20
    )


    for item in reversed(history):

        intent = item.get(
            "intent"
        )


        if intent in sales_intents:

            return intent


    return None



# =====================================================
# LAST SUPPORT INTENT
# =====================================================

def get_last_support_intent(
    customer_id:int
):

    history = get_chat_history(
        customer_id,
        20
    )


    for item in reversed(history):

        intent = item.get(
            "intent"
        )


        if (
            intent
            and intent not in
            [
                "buy_product",
                "software_sales",
                "ai_assistant"
            ]
        ):

            return intent


    return None



# =====================================================
# CONVERSATION STAGE
# =====================================================

def get_conversation_stage(
    customer_id:int
):

    last_sales = get_last_sales_intent(
        customer_id
    )


    history = get_chat_history(
        customer_id,
        10
    )


    messages = [
        x.get(
            "message_content",
            ""
        ).lower()

        for x in history
    ]



    if last_sales:

        if any(
            word in " ".join(messages)
            for word in [
                "precio",
                "valor",
                "fotos",
                "detalles"
            ]
        ):

            return "product_evaluation"


        if any(
            word in " ".join(messages)
            for word in [
                "comprar",
                "reservar",
                "quiero ese"
            ]
        ):

            return "checkout"


        return "sales_discovery"



    return "support"



# =====================================================
# COMPLETE MEMORY STATE
# =====================================================

def get_memory_state(
    customer_id:int
):

    return {

        "last_intent":
            get_last_intent(
                customer_id
            ),

        "last_sales_intent":
            get_last_sales_intent(
                customer_id
            ),

        "last_support_intent":
            get_last_support_intent(
                customer_id
            ),

        "conversation_stage":
            get_conversation_stage(
                customer_id
            )
    }



# =====================================================
# COMPATIBILITY ALIASES
# =====================================================

def obtener_memoria(
    cliente_id
):

    return build_memory_context(
        cliente_id
    )



def obtener_historial_chat(
    cliente_id
):

    return get_chat_history(
        cliente_id
    )
    # =====================================================
# BITEY CORE COMPATIBILITY
# =====================================================

def get_customer_memory(
    customer_id: int,
    limit: int = 5
):
    """
    Returns customer conversational memory.
    Used by Bitey Core.
    """

    return build_memory_context(
        customer_id,
        limit
    )
    # =====================================================
# BITEY CORE COMPATIBILITY
# =====================================================

def get_customer_memory(
    customer_id: int,
    limit: int = 5
):
    """
    Returns customer conversational memory.
    Used by Bitey Core.
    """

    return build_memory_context(
        customer_id,
        limit
    )
# =====================================================
# CLEAR CUSTOMER MEMORY
# =====================================================

def clear_customer_memory(customer_id: int):

    try:

        result = (
            database
            .table("messages")
            .delete()
            .eq(
                "customer_id",
                customer_id
            )
            .execute()
        )

        return {
            "success": True,
            "deleted": result.data
        }


    except Exception as error:

        print(
            "[CLEAR MEMORY ERROR]",
            error
        )

        return {
            "success": False,
            "error": str(error)
        }