"""
BiteFixes Knowledge Service

Searches Bitey's knowledge base.

Priority:

1. Intent match
2. Language match
3. Keyword relevance
4. Fallback
"""


from app.database.supabase import database



def search_knowledge(
    message: str,
    company_id: int = None,
    intent: str = None,
    language: str = None
):


    try:


        if not message:
            return None



        query = (
            database
            .table("knowledge_base")
            .select("*")
            .eq(
                "is_active",
                True
            )
        )



        if company_id:


            query = query.eq(
                "company_id",
                company_id
            )



        result = (
            query
            .execute()
        )



        items = result.data or []



        if not items:

            return None



        # ==========================
        # INTENT MATCH
        # ==========================


        if intent:


            matches = [

                item

                for item in items

                if item.get("intent")
                ==
                intent

            ]


            if matches:

                items = matches



        # ==========================
        # LANGUAGE MATCH
        # ==========================


        if language:


            lang_matches = [

                item

                for item in items

                if item.get("language")
                ==
                language

            ]


            if lang_matches:

                items = lang_matches




        # ==========================
        # KEYWORD SEARCH
        # ==========================


        words = [

            w.strip(".,!?;:")

            for w in message.lower().split()

            if len(w) >= 3

        ]



        best = None

        score_best = 0



        for item in items:


            content = " ".join([


                str(item.get("title","")),


                str(item.get("question","")),


                str(item.get("answer","")),


                str(item.get("keywords",""))


            ]).lower()



            score = 0



            for word in words:


                if word in content:

                    score += 1



            if score > score_best:


                score_best = score

                best = item



        if best:

            return best



        return items[0]



    except Exception as error:


        print(
            "[KNOWLEDGE ERROR]",
            error
        )


        return None





def find_knowledge(
    message,
    company_id=None,
    intent=None,
    language=None
):


    return search_knowledge(
        message,
        company_id,
        intent,
        language
    )