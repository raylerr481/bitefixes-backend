"""
Bitey Default Intent Knowledge

Initial AI brain training data.
"""


from app.supabase_client import supabase



DEFAULT_INTENTS = [


# Hardware

{
"intent":"hardware_upgrade",
"keyword":"upgrade notebook",
"weight":5
},

{
"intent":"hardware_upgrade",
"keyword":"aumentar ram",
"weight":5
},

{
"intent":"hardware_upgrade",
"keyword":"trocar ssd",
"weight":5
},



# Repair

{
"intent":"computer_repair",
"keyword":"notebook lento",
"weight":5
},

{
"intent":"computer_repair",
"keyword":"computador nao liga",
"weight":5
},



# Remote support

{
"intent":"remote_support",
"keyword":"suporte remoto",
"weight":5
},

{
"intent":"remote_support",
"keyword":"ajuda remota",
"weight":4
},



# AI Assistant

{
"intent":"ai_assistant",
"keyword":"assistente ia",
"weight":5
},

{
"intent":"ai_assistant",
"keyword":"inteligencia artificial",
"weight":5
},

{
"intent":"ai_assistant",
"keyword":"chatbot empresa",
"weight":5
},

{
"intent":"ai_assistant",
"keyword":"automatizar empresa",
"weight":4
},



# Sales

{
"intent":"buy_product",
"keyword":"comprar notebook",
"weight":5
},

{
"intent":"buy_product",
"keyword":"notebook usado",
"weight":4
}

]



def seed_intents():

    inserted = 0


    for item in DEFAULT_INTENTS:


        exists = (
            supabase
            .table("sinonimos_ia")
            .select("id")
            .eq(
                "intent",
                item["intent"]
            )
            .eq(
                "keyword",
                item["keyword"]
            )
            .execute()
        )


        if exists.data:

            continue



        supabase.table(
            "sinonimos_ia"
        ).insert(
            item
        ).execute()


        inserted += 1



    return {

        "inserted": inserted

    }