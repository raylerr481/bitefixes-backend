"""
BiteFixes Prompt Builder
"""


from app.services.ia_engine import analyze_message



SYSTEM_PROMPT = """

You are Bitey.

Virtual assistant of BiteFixes.

Provide useful technical and commercial help.

Never create fake services.

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


    prompt = {


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


    return prompt