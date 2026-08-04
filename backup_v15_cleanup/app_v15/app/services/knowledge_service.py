"""
Knowledge Service
Search answers from knowledge_base.

Priority:
1. Exact intent match
2. Keyword match
3. Return None
"""

from app.database.supabase import database


def search_knowledge(
    message: str,
    company_id: int = 1,
    intent: str = None
):
    """
    Returns:
    {
        "answer": "...",
        "requires_ticket": True,
        ...
    }
    """

    try:

        # -----------------------------
        # Search by intent
        # -----------------------------

        if intent:

            result = (
                database
                .table("knowledge_base")
                .select("*")
                .eq("company_id", company_id)
                .eq("intent", intent)
                .limit(1)
                .execute()
            )

            if result.data:
                return result.data[0]

        # -----------------------------
        # Keyword search
        # -----------------------------

        words = [
            w.strip().lower()
            for w in message.split()
            if len(w.strip()) >= 3
        ]

        if not words:
            return None

        result = (
            database
            .table("knowledge_base")
            .select("*")
            .eq("company_id", company_id)
            .execute()
        )

        rows = result.data or []

        best = None
        score = 0

        for row in rows:

            text = (
                (
                    row.get("question") or ""
                )
                + " "
                + (
                    row.get("keywords") or ""
                )
            ).lower()

            points = sum(
                1
                for word in words
                if word in text
            )

            if points > score:
                score = points
                best = row

        if best:
            return best

        return None

    except Exception as error:

        print(
            "[KNOWLEDGE ERROR]",
            error
        )

        return None


# -----------------------------------
# Compatibility aliases
# -----------------------------------

def buscar_conocimiento(
    mensaje,
    company_id=1,
    intent=None
):
    return search_knowledge(
        mensaje,
        company_id,
        intent
    )


def get_answer(
    message,
    company_id=1,
    intent=None
):
    return search_knowledge(
        message,
        company_id,
        intent
    )