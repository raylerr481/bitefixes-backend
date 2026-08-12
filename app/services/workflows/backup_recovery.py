from app.database.supabase import supabase


def get_knowledge_by_intent(
    empresa_id: int,
    intent: str
):
    """
    Search knowledge base by detected intent.
    """

    response = (
        supabase
        .table("base_conhecimento")
        .select("*")
        .eq("empresa_id", empresa_id)
        .eq("intencion", intent)
        .eq("activo", True)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None



def search_knowledge(
    empresa_id: int,
    query: str
):
    """
    Search knowledge base by text.
    """

    response = (
        supabase
        .table("base_conhecimento")
        .select("*")
        .eq("empresa_id", empresa_id)
        .eq("activo", True)
        .execute()
    )


    if not response.data:
        return None


    query_lower = query.lower()


    for item in response.data:

        text = " ".join([

            str(item.get("titulo", "")),

            str(item.get("pregunta", "")),

            str(item.get("tags", ""))

        ]).lower()


        if any(
            word in text
            for word in query_lower.split()
        ):

            return item


    return None



def buscar_conocimiento(
    empresa_id: int,
    mensaje: str
):
    """
    Compatibility function used by Bitey.
    """

    return search_knowledge(
        empresa_id,
        mensaje
    )



def get_all_knowledge(
    empresa_id: int
):
    """
    Return company knowledge base.
    """

    response = (
        supabase
        .table("base_conhecimento")
        .select("*")
        .eq("empresa_id", empresa_id)
        .eq("activo", True)
        .execute()
    )

    return response.data



def create_knowledge(
    data: dict
):
    """
    Create knowledge entry.
    """

    response = (
        supabase
        .table("base_conhecimento")
        .insert(data)
        .execute()
    )

    return response.data[0] if response.data else None