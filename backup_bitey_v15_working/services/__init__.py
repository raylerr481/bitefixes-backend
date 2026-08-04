from app.database.supabase import supabase_manager
from datetime import datetime



def get_or_create_customer(
    company_id:int,
    phone:str,
    name:str="Unknown"
):

    db = supabase_manager.get_client()


    result = (
        db
        .table("customers")
        .select("*")
        .eq("company_id",company_id)
        .eq("phone",phone)
        .execute()
    )


    if result.data:

        return result.data[0]


    customer = {

        "company_id":company_id,

        "phone":phone,

        "name":name,

        "created_at":
            datetime.utcnow().isoformat()

    }


    created = (
        db
        .table("customers")
        .insert(customer)
        .execute()
    )


    return created.data[0]