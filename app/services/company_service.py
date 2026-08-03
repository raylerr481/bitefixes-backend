from app.supabase_client import supabase


def get_company(empresa_id: int):
    """
    Get company information by company id.
    """

    response = (
        supabase
        .table("companies")
        .select("*")
        .eq("id", empresa_id)
        .single()
        .execute()
    )

    return response.data



def get_company_services(empresa_id: int):
    """
    Get active services available for a company.
    """

    response = (
        supabase
        .table("servicios")
        .select("*")
        .eq("empresa_id", empresa_id)
        .eq("activo", True)
        .execute()
    )

    return response.data



def get_company_knowledge(empresa_id: int):
    """
    Get knowledge base entries for a company.
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



def get_company_context(empresa_id: int):
    """
    Build complete context used by Bitey AI.
    """

    company = get_company(empresa_id)

    services = get_company_services(empresa_id)

    knowledge = get_company_knowledge(empresa_id)


    return {
        "company": company,
        "services": services,
        "knowledge": knowledge
    }