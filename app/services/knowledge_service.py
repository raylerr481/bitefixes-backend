"""
BiteFixes Knowledge Service V2

Responsibilities:

- Search knowledge base
- Multilingual answers
- Intent priority
- Tag matching
- Keyword ranking
- AI context support

Priority:

1. Intent + language
2. Intent
3. Keyword score
4. Return None
"""


from app.database.supabase import database


def normalize_text(text):

    if not text:
        return ""

    return (
        str(text)
        .lower()
        .replace("á","a")
        .replace("é","e")
        .replace("í","i")
        .replace("ó","o")
        .replace("ú","u")
        .replace("ã","a")
        .replace("õ","o")
        .replace("ç","c")
        .strip()
    )



def calculate_score(message,row):

    message = normalize_text(message)

    score = 0


    fields = [

        row.get("title"),

        row.get("question"),

        row.get("answer"),

    ]


    tags = row.get("tags")


    if isinstance(tags,list):

        fields.extend(tags)


    elif tags:

        fields.append(tags)



    text = normalize_text(
        " ".join(
            [
                str(x)
                for x in fields
                if x
            ]
        )
    )



    words = message.split()



    for word in words:

        if len(word)<3:
            continue


        if word in text:

            score += 5



    return score





def search_knowledge(
        message:str,
        company_id:int=1,
        intent:str=None,
        language:str=None
):


    try:


        rows = (

            database

            .table("knowledge_base")

            .select("*")

            .eq(
                "company_id",
                company_id
            )

            .eq(
                "is_active",
                True
            )

            .execute()

            .data

        )


        if not rows:

            return None



        # ----------------------------
        # Intent + Language
        # ----------------------------


        if intent:


            for row in rows:


                if row.get("intent") != intent:

                    continue



                row_language = row.get(
                    "language"
                )



                if language and row_language:

                    if row_language == language:

                        return row



        # ----------------------------
        # Intent only
        # ----------------------------


        if intent:


            for row in rows:


                if row.get("intent")==intent:

                    return row



        # ----------------------------
        # Keyword ranking
        # ----------------------------


        best = None

        best_score = 0



        for row in rows:


            score = calculate_score(
                message,
                row
            )



            if score > best_score:

                best_score = score

                best = row



        if best_score >=5:

            return best



        return None



    except Exception as error:


        print(
            "[KNOWLEDGE SERVICE ERROR]",
            error
        )


        return None





# Compatibility

def buscar_conocimiento(
        mensaje,
        company_id=1,
        intent=None,
        language=None
):

    return search_knowledge(
        mensaje,
        company_id,
        intent,
        language
    )



def get_answer(
        message,
        company_id=1,
        intent=None,
        language=None
):

    return search_knowledge(
        message,
        company_id,
        intent,
        language
    )