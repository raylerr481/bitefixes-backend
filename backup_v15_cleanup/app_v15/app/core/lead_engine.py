"""
BiteFixes Lead Engine V1

Commercial intelligence layer.

Responsibilities:

- Detect sales opportunities
- Qualify customers
- Track commercial stage
- Prepare CRM data
"""


COMMERCIAL_INTENTS = [

    "ai_assistant",
    "buy_product",
    "software_sales"

]



def analyze_lead(

    intent,

    message,

    customer_id,

    context=None

):


    lead = {

        "is_lead": False,

        "lead_type": None,

        "customer_id": customer_id,

        "stage": None,

        "score": 0,

        "data": {}

    }



    # =====================
    # Detect commercial intent
    # =====================


    if intent in COMMERCIAL_INTENTS:


        lead["is_lead"] = True


        lead["lead_type"] = intent


        lead["score"] += 50



    else:


        return lead




    # =====================
    # Basic qualification
    # =====================


    text = message.lower()



    company_words = [

        "empresa",

        "negocio",

        "tienda",

        "empresa",

        "clientes",

        "equipo"

    ]



    for word in company_words:


        if word in text:


            lead["score"] += 10


            lead["data"][

                "business_context"

            ] = True


            break




    # =====================
    # Sales stage
    # =====================


    if lead["score"] >= 60:


        lead["stage"] = "qualified"



    else:


        lead["stage"] = "discovery"




    return lead