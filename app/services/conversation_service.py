"""BiteFixes conversation lifecycle and context persistence."""
from datetime import datetime, timezone
from typing import Any
from app.database.supabase import database

def _now()->str:return datetime.now(timezone.utc).isoformat()

def _db_conversation_id(value:Any):
    """Return a database conversation id only when the supplied value is numeric."""
    try:
        text=str(value or "").strip()
        return int(text) if text.isdigit() else None
    except (TypeError,ValueError):
        return None

def get_or_create_conversation(customer_id:int,channel:str="website",conversation_id:Any=None):
    """Resolve the active conversation for this customer and channel.

    Channel adapters may provide an external conversation identifier (for
    example a WhatsApp conversation id). The Supabase conversations.id column
    is a bigint, so non-numeric external identifiers must never be used as the
    database id filter. In that case the active customer/channel conversation
    is resolved instead.
    """
    try:
        channel=str(channel or "website").strip().lower()
        query=database.table("conversations").select("*").eq("customer_id",customer_id).eq("channel",channel).eq("status","active")
        db_cid=_db_conversation_id(conversation_id)
        if db_cid is not None:
            query=query.eq("id",db_cid)
        result=query.order("updated_at",desc=True).limit(1).execute()
        if result.data:return result.data[0]
        conversation={"customer_id":customer_id,"channel":channel,"status":"active","agent":"bitey","handled_by_ai":True,"requires_human":False,"created_at":_now(),"updated_at":_now()}
        result=database.table("conversations").insert(conversation).execute();return result.data[0] if result.data else None
    except Exception as error:
        print("[CREATE CONVERSATION ERROR]",type(error).__name__,error);return None

def get_conversation(conversation_id:Any,customer_id:int|None=None):
    """Return conversation context enriched with the latest problem for THIS conversation."""
    try:
        query=database.table("conversations").select("*").eq("id",conversation_id)
        if customer_id is not None:query=query.eq("customer_id",customer_id)
        result=query.limit(1).execute()
        if not result.data:return None
        conversation=dict(result.data[0])
        try:
            problem_q=database.table("bitey_problems").select("*").eq("conversation_id",conversation_id).order("last_seen_at",desc=True).limit(1).execute()
            if problem_q.data:
                p=problem_q.data[0]
                conversation.update({"last_problem":p.get("problem_summary") or p.get("category"),"last_problem_category":p.get("category"),"last_problem_id":p.get("id"),"last_problem_fingerprint":p.get("fingerprint"),"last_device":p.get("device_label"),"last_platform":p.get("device_platform"),"last_problem_state":p.get("state"),"last_problem_confidence":p.get("confidence")})
        except Exception as problem_error:
            print("[CONVERSATION PROBLEM CONTEXT WARNING]",type(problem_error).__name__,problem_error)
        return conversation
    except Exception as error:
        print("[GET CONVERSATION ERROR]",type(error).__name__,error);return None

def update_conversation(conversation_id:Any,data:dict):
    try:
        allowed_fields={"ticket_id","agent","last_intent","last_response","last_service","last_confidence","handled_by_ai","requires_human","status","closed_at","language","updated_at"}
        clean_data={k:v for k,v in data.items() if k in allowed_fields}
        if not clean_data:return None
        clean_data["updated_at"]=_now()
        result=database.table("conversations").update(clean_data).eq("id",conversation_id).execute();return result.data[0] if result.data else None
    except Exception as error:
        print("[UPDATE CONVERSATION ERROR]",type(error).__name__,error);return None

def close_conversation(conversation_id:Any):return update_conversation(conversation_id,{"status":"closed","closed_at":_now()})

def update_conversation_context(conversation_id:Any,intent:str=None,response:str=None,ticket_id:int=None,service_id:int=None,confidence:float=None,language:str=None,metadata:dict=None):
    """Persist supported conversation fields and accept metadata for compatibility.
    Problem state itself is persisted in bitey_problems; metadata is intentionally
    not written to conversations because that table may not expose a metadata column.
    """
    data={}
    if intent:data["last_intent"]=intent
    if response:data["last_response"]=response
    if ticket_id is not None:data["ticket_id"]=ticket_id
    if service_id is not None:data["last_service"]=service_id
    if confidence is not None:data["last_confidence"]=float(confidence)
    if language:data["language"]=language
    return update_conversation(conversation_id,data)

def obtener_o_crear_conversacion(customer_id,channel="website"):return get_or_create_conversation(customer_id,channel)
def actualizar_conversacion(conversation_id,datos):return update_conversation(conversation_id,datos)
def cerrar_conversacion(conversation_id):return close_conversation(conversation_id)
