from app.database.supabase import supabase


tables = [
    "base_conhecimento",
    "base_conocimiento",
    "knowledge_base",
    "conocimiento",
    "conhecimentos",
    "sinonimos_ia",
    "clientes",
    "tickets",
    "servicios",
    "servicos"
]


for table in tables:

    try:

        result = (
            supabase
            .table(table)
            .select("*")
            .limit(1)
            .execute()
        )

        print(
            "\nOK TABLE:",
            table
        )

        print(
            result.data
        )


    except Exception as error:

        print(
            "\nERROR TABLE:",
            table
        )

        print(
            error
        )