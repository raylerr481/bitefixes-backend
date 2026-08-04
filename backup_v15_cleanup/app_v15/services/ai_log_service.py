"""
BiteFixes AI Log Service

Stores Bitey AI decisions.
Tracks:
- message
- intent
- confidence
- knowledge usage
- response
- model
"""

from app.database.supabase import database


def create_ai_log(
    company_id,
    conversation_id,
    input_message,
    detected_intent=None,
    confidence=0,
    knowledge_found=False,
    knowledge_id=None,
    ai_response=None,
    model_used="bitey_engine"
):

    try:

        data = {

            "company_id": company_id,

            "conversation_id": conversation_id,

            "input_message": input_message,

            "detected_intent": detected_intent,

            "confidence": confidence,

            "knowledge_found": knowledge_found,

            "knowledge_id": knowledge_id,

            "ai_response": ai_response,

            "model_used": model_used

        }


        result = (
            database
            .table("ai_logs")
            .insert(data)
            .execute()
        )


        if result.data:

            return result.data[0]


        return None


    except Exception as error:

        print(
            "[AI LOG ERROR]",
            error
        )

        return None