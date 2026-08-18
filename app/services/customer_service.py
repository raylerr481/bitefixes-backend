"""Customer management for Bitey channels."""

from datetime import datetime
from app.database.supabase import database


def _clean(value):
    return str(value or "").strip()


def get_customer_by_phone(phone: str, company_id: int = 1):
    try:
        phone = _clean(phone)
        if not phone:
            return None
        result = (
            database.table("customers")
            .select("*")
            .eq("company_id", company_id)
            .eq("phone", phone)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as error:
        print("[CUSTOMER LOOKUP ERROR]", error)
        return None


def create_customer(company_id: int, phone: str, name: str = "Customer"):
    try:
        customer = {
            "company_id": company_id,
            "full_name": _clean(name) or "Customer",
            "phone": _clean(phone),
            "preferred_language": "pt-BR",
            "customer_type": "individual",
            "is_active": True,
            "last_access": datetime.utcnow().isoformat(),
        }
        result = database.table("customers").insert(customer).execute()
        return result.data[0] if result.data else None
    except Exception as error:
        print("[CUSTOMER CREATE ERROR]", error)
        return None


def update_customer_from_chat(customer: dict, name: str = "", phone: str = ""):
    """Persist the latest non-empty customer identity supplied by a channel."""
    if not customer or not customer.get("id"):
        return customer

    supplied_name = _clean(name)
    supplied_phone = _clean(phone)
    current_name = _clean(customer.get("full_name"))
    current_phone = _clean(customer.get("phone"))
    updates = {"last_access": datetime.utcnow().isoformat()}

    if supplied_name and supplied_name.lower() not in {"customer", "cliente", "customer name"}:
        if not current_name or current_name.lower() in {"customer", "cliente"} or current_name != supplied_name:
            updates["full_name"] = supplied_name

    if supplied_phone and supplied_phone.lower() not in {"web", "unknown"} and supplied_phone != current_phone:
        updates["phone"] = supplied_phone

    try:
        result = database.table("customers").update(updates).eq("id", customer["id"]).execute()
        return result.data[0] if result.data else {**customer, **updates}
    except Exception as error:
        print("[CUSTOMER UPDATE WARNING]", error)
        return {**customer, **updates}


def get_or_create_customer(company_id: int, phone: str, name: str = "Customer"):
    customer = get_customer_by_phone(phone, company_id)
    if customer:
        return update_customer_from_chat(customer, name=name, phone=phone)
    return create_customer(company_id, phone, name)


def get_customer_by_whatsapp(whatsapp: str, company_id: int = 1):
    return get_customer_by_phone(whatsapp, company_id)


def get_customer_by_channel(channel: str, value: str, company_id: int = 1):
    if not value:
        return None
    if channel.lower() in ["whatsapp", "phone", "website"]:
        return get_customer_by_phone(value, company_id)
    return None
