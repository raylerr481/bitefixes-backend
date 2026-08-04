"""
BiteFixes Product Service V2

Product catalog access.

Responsibilities:
- Read products from Supabase
- Search inventory
- Format products for Bitey sales flow
"""

from app.database.supabase import database



def get_available_products(
    company_id: int,
    limit: int = 5
):
    """
    Get available products.
    """

    try:

        result = (
            database
            .table("products")
            .select("*")
            .eq(
                "company_id",
                company_id
            )
            .eq(
                "status",
                "available"
            )
            .limit(
                limit
            )
            .execute()
        )


        return result.data or []


    except Exception as error:

        print(
            "[PRODUCT LIST ERROR]",
            error
        )

        return []



def search_products(
    company_id: int,
    keyword: str
):
    """
    Search products by text.
    """

    try:

        products = get_available_products(
            company_id,
            100
        )


        keyword = (
            keyword
            .lower()
            .strip()
        )


        matches = []


        for product in products:


            searchable = " ".join([

                str(product.get("name", "")),

                str(product.get("brand", "")),

                str(product.get("model", "")),

                str(product.get("category", ""))

            ]).lower()



            if keyword in searchable:

                matches.append(
                    product
                )


        return matches



    except Exception as error:


        print(
            "[PRODUCT SEARCH ERROR]",
            error
        )


        return []



def format_product(
    product: dict
):
    """
    Format product information.
    """

    return {

        "name":
            product.get("name"),


        "brand":
            product.get("brand"),


        "model":
            product.get("model"),


        "price":
            product.get("price"),


        "ram":
            product.get("ram"),


        "storage":
            product.get("storage"),


        "processor":
            product.get("processor")

    }