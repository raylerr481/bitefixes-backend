"""Customer identity management for all Bitey channels."""

from datetime import datetime, timezone
from app.database.supabase import database


def _clean(value):
    return str(value or "").strip()


def _channel_column(channel: str | None) -> str | None:
    value = _clean(channel).lower()
    return {
        "website": "website_session",
        "telegram": "telegram",
        "whatsapp": "whatsapp",
        "messenger": "messenger",
        "instagram": "instagram",
    }.get(value)


def get_customer_by_phone(phone: str, company_id: int = 1):
    try:
        phone = _clean(phone)
        if not phone:
            return None
        result = database.table("customers").select("*").eq("company_id", company_id).eq("phone", phone).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as error:
        print("[CUSTOMER LOOKUP ERROR]", error)
        return None


def get_customer_by_channel(channel: str, value: str, company_id: int = 1):
    """Resolve a customer by the stable identifier belonging to a channel."""
    value = _clean(value)
    if not value:
        return None
    column = _channel_column(channel)
    try:
        if column:
            result = (database.table("customers").select("*")
                      .eq("company_id", company_id)
                      .eq(column, value)
                      .limit(1).execute())
            if result.data:
                return result.data[0]
        if channel in {"whatsapp", "phone"}:
            return get_customer_by_phone(value, company_id)
    except Exception as error:
        print("[CUSTOMER CHANNEL LOOKUP ERROR]", error)
    return None


def create_customer(company_id: int, phone: str, email: str = "", name: str = "Customer", channel: str = "website", external_id: str = "", last_name: str = ""):
    try:
        phone = _clean(phone)
        email = _clean(email).lower()
        external_id = _clean(external_id)
        first_name = _clean(name) or "Customer"
        surname = _clean(last_name)
        full_name = " ".join(part for part in [first_name, surname] if part)
        customer = {
            "company_id": company_id,
            "full_name": full_name,
            "phone": phone,
            "email": email,
            "preferred_language": "pt-BR",
            "customer_type": "individual",
            "is_active": True,
            "last_access": datetime.now(timezone.utc).isoformat(),
        }
        column = _channel_column(channel)
        if column and external_id:
            customer[column] = external_id
        if external_id and channel not in {"website", "telegram", "whatsapp", "messenger", "instagram"}:
            customer["external_id"] = external_id
        result = database.table("customers").insert(customer).execute()
        return result.data[0] if result.data else None
    except Exception as error:
        print("[CUSTOMER CREATE ERROR]", error)
        return None


def update_customer_from_chat(customer: dict, name: str = "", last_name: str = "", phone: str = "", email: str = "", channel: str = "", external_id: str = ""):
    if not customer or not customer.get("id"):
        return customer
    supplied_name = _clean(name)
    supplied_last_name = _clean(last_name)
    supplied_phone, supplied_email = _clean(phone), _clean(email).lower()
    external_id = _clean(external_id)
    current_name, current_phone, current_email = _clean(customer.get("full_name")), _clean(customer.get("phone")), _clean(customer.get("email"))
    updates = {"last_access": datetime.now(timezone.utc).isoformat()}
    if supplied_name and supplied_name.lower() not in {"customer", "cliente", "customer name"}:
        candidate = " ".join(part for part in [supplied_name, supplied_last_name] if part)
        if candidate and candidate != current_name:
            updates["full_name"] = candidate
    if supplied_phone and supplied_phone.lower() not in {"web", "unknown"} and supplied_phone != current_phone:
        updates["phone"] = supplied_phone
    if supplied_email and supplied_email != current_email:
        updates["email"] = supplied_email
    column = _channel_column(channel)
    if column and external_id and _clean(customer.get(column)) != external_id:
        updates[column] = external_id
    try:
        result = database.table("customers").update(updates).eq("id", customer["id"]).execute()
        return result.data[0] if result.data else {**customer, **updates}
    except Exception as error:
        print("[CUSTOMER UPDATE WARNING]", error)
        return {**customer, **updates}


def get_or_create_customer(company_id: int, phone: str, email: str = "", name: str = "Customer", last_name: str = "", channel: str = "", external_id: str = ""):
    """Resolve identity by stable channel identifier first, then phone/email."""
    channel = _clean(channel).lower()
    external_id = _clean(external_id)
    phone = _clean(phone)
    email = _clean(email).lower()
    identity = external_id or phone
    customer = get_customer_by_channel(channel, identity, company_id) if channel and identity else None
    if not customer and phone:
        customer = get_customer_by_phone(phone, company_id)
    if not customer and email:
        try:
            result = database.table("customers").select("*").eq("company_id", company_id).eq("email", email).limit(1).execute()
            customer = result.data[0] if result.data else None
        except Exception as error:
            print("[CUSTOMER EMAIL LOOKUP WARNING]", type(error).__name__)
    if customer:
        return update_customer_from_chat(customer, name=name, last_name=last_name, phone=phone, email=email, channel=channel, external_id=external_id)
    return create_customer(company_id, phone, email, name, channel=channel, external_id=external_id, last_name=last_name)


def get_customer_by_whatsapp(whatsapp: str, company_id: int = 1):
    return get_customer_by_channel("whatsapp", whatsapp, company_id) or get_customer_by_phone(whatsapp, company_id)
