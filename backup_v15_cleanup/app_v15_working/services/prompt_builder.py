"""
BiteFixes Prompt Builder

Creates a structured prompt for any LLM.
"""

from app.services.ia_engine import analyze_message


SYSTEM_PROMPT = """
You are Bitey.

You are the virtual AI assistant of BiteFixes.

Your goals:

- Answer professionally.
- Be concise.
- Use company knowledge.
- Recommend services.
- Help customers.
- Never invent services.
"""


def build_prompt(
    message,
    memory,
    last_intent=None,
    service=None,
    knowledge=None
):

    analysis = analyze_message(message)

    prompt = {

        "system": SYSTEM_PROMPT,

        "message": message,

        "normalized": analysis["normalized"],

        "words": analysis["words"],

        "last_intent": last_intent,

        "memory": memory,

        "service": service,

        "knowledge": knowledge

    }

    return prompt