"""
BiteFixes Reasoning Engine V6

Decision layer for Bitey AI.

Responsibilities:
- Select workflow
- Decide sales/support behavior
- Decide ticket creation
- Decide ticket reuse
- Use products
- Recommend services
"""

SALES_INTENTS = [
    "buy_product",
    "software_sales",
    "ai_assistant"
]


SUPPORT_INTENTS = [
    "computer_repair",
    "hardware_upgrade",
    "network_problem",
    "security_issue"
]


def analyze_context(
    context,
    intent,
    knowledge=None,
    service=None,
    existing_ticket=None
):

    decision = {

        "action": "general_assistance",

        "create_ticket": False,

        "reuse_ticket": False,

        "human_required": False,

        "use_knowledge": False,

        "use_products": False,

        "recommend_service": False,

        "workflow": "support",

        "reason": []

    }


    # =========================
    # SALES FLOW
    # =========================

    if intent in SALES_INTENTS:


        decision["workflow"] = "sales"


        # =====================
        # PRODUCT SALES
        # =====================

        if intent == "buy_product":


            products = context.get(
                "product_recommendations",
                []
            )


            if products:


                decision["action"] = (
                    "product_sales"
                )


                decision["use_products"] = True


                decision["reason"].append(
                    "Commercial intent detected"
                )


                decision["reason"].append(
                    "Products available"
                )


            else:


                decision["action"] = (
                    "sales_assistance"
                )


                decision["use_knowledge"] = True


                decision["reason"].append(
                    "No products available"
                )



        # =====================
        # SERVICE SALES
        # =====================

        else:


            decision["action"] = (
                "service_sales"
            )


            decision["use_knowledge"] = True


            services = context.get(
                "service_recommendations",
                []
            )


            if services:


                decision["recommend_service"] = True


                decision["reason"].append(
                    "Service matched"
                )


            decision["reason"].append(
                "Commercial service request"
            )



        return decision



    # =========================
    # SUPPORT FLOW
    # =========================

    decision["workflow"] = "support"



    if knowledge:


        decision["use_knowledge"] = True


        decision["reason"].append(
            "Knowledge base available"
        )



    if service:


        decision["recommend_service"] = True


        decision["reason"].append(
            "Service matched"
        )



    # =========================
    # TICKET INTELLIGENCE
    # =========================


    memory_state = context.get(
        "memory_state",
        {}
    )


    last_support_intent = (
        memory_state.get(
            "last_support_intent"
        )
    )



    # =========================
    # REUSE EXISTING TICKET
    # =========================


    if existing_ticket and (
        last_support_intent == intent
    ):


        decision["action"] = (
            "ticket_followup"
        )


        decision["reuse_ticket"] = True


        decision["reason"].append(
            "Same support issue detected"
        )


        return decision



    # =========================
    # NEW TECHNICAL REQUEST
    # =========================


    if service:


        decision["action"] = (
            "technical_support"
        )


        decision["create_ticket"] = True


        decision["reason"].append(
            "New support request"
        )


    return decision