"""
Knowledge Service

Bitey knowledge retrieval layer.
"""

from app.database.supabase import supabase_manager


def search_knowledge(
    company_id: int,
    message: str
):

    db = supabase_manager.get_client()

    text = message.lower()

    try:

        result = (
            db
            .table("knowledge_base")
            .select("*")
            .eq(
                "company_id",
                company_id
            )
            .execute()
        )


        items = result.data or []


        best_match = None
        best_score = 0


        for item in items:

            score = 0


            fields = [
                item.get("title"),
                item.get("question"),
                item.get("answer"),
                item.get("keywords")
            ]


            content = " ".join(
                str(x)
                for x in fields
                if x
            ).lower()


            for word in text.split():

                if len(word) > 3 and word in content:
                    score += 1


            if score > best_score:

                best_score = score
                best_match = item



        if best_match:

            return {
                "found": True,
                "score": best_score,
                "data": best_match
            }



        return {
            "found": False,
            "score": 0,
            "data": None
        }


    except Exception as e:

        print(
            "[KNOWLEDGE ERROR]",
            e
        )

        return {
            "found": False,
            "score": 0,
            "data": None
        }