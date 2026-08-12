"""
BiteFixes LLM Service

Prompt preparation layer.
"""


from app.services.ia_engine import analyze_message



SYSTEM_PROMPT = """

You are Bitey.

You are the virtual AI assistant of BiteFixes.

Rules:

- Answer professionally.
- Be concise.
- Use company knowledge.
- Recommend only existing services.
- Never invent services.

"""



def build_prompt(
    message,
    memory=None,
    last_intent=None,
    service=None,
    knowledge=None
):


    analysis = analyze_message(
        message
    )


    return {


        "system":
            SYSTEM_PROMPT,


        "message":
            message,


        "normalized":
            analysis["normalized"],


        "words":
            analysis["words"],


        "last_intent":
            last_intent,


        "memory":
            memory,


        "service":
            service,


        "knowledge":
            knowledge

    }