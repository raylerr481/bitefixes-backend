import os
from typing import Dict, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = "https://iwgcekvasxizdekjiacg.supabase.co"
SUPABASE_KEY = "sb_secret_b082pBn6YNA9rwPrDM20RA_AYzjYJRh"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan configurar las variables de entorno SUPABASE_URL y/AS SUPABASE_KEY.")

def get_supabase() -> Client:
    """
    Inicializa y retorna el cliente oficial de Supabase.
    """
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def verificar_cliente_por_whatsapp(numero_whatsapp: str) -> Optional[Dict[str, Any]]:
    """
    Busca si el número de WhatsApp ya existe en la tabla 'clientes'.
    Retorna el diccionario con la información del cliente o None si no existe.
    """
    supabase = get_supabase()
    # Limpiamos el número de espacios y signos comunes en WhatsApp
    clean_number = numero_whatsapp.replace(" ", "").replace("-", "").strip()
    
    try:
        response = supabase.table("clientes")\
            .select("id, nombre, whatsapp, direccion")\
            .eq("whatsapp", clean_number)\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error al verificar cliente por whatsapp: {str(e)}")
        # En producción se debe registrar este error mediante logs formales (e.g. Logfire o Sentry)
        return None

def registrar_cliente_nuevo(nombre: str, whatsapp: str, direccion: str) -> Dict[str, Any]:
    """
    Registra un nuevo cliente en la tabla 'clientes' de Supabase.
    Retorna los datos del cliente recién insertado.
    """
    supabase = get_supabase()
    clean_number = whatsapp.replace(" ", "").replace("-", "").strip()
    
    nuevo_cliente = {
        "nombre": nombre.strip(),
        "whatsapp": clean_number,
        "direccion": direccion.strip()
    }
    
    try:
        response = supabase.table("clientes")\
            .insert(nuevo_cliente)\
            .execute()
            
        if response.data and len(response.data) > 0:
            return response.data[0]
        raise Exception("No se retornaron datos tras la inserción del cliente.")
    except Exception as e:
        error_msg = f"Error al registrar cliente nuevo: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

def crear_ticket_soporte(cliente_id: str, categoria: str, descripcion: str) -> Dict[str, Any]:
    """
    Crea un nuevo ticket de soporte técnico en la tabla 'tickets' de Supabase.
    Estatus por defecto al iniciar es 'Abierto'.
    """
    supabase = get_supabase()
    
    # Validar categorías válidas para control
    categorias_validas = ["Hardware", "Software", "Redes", "Comercial", "Otro"]
    if categoria not in categorias_validas:
        categoria = "Otro"
        
    nuevo_ticket = {
        "cliente_id": cliente_id,
        "categoria": categoria,
        "descripcion": descripcion.strip(),
        "estatus": "Abierto"
    }
    
    try:
        response = supabase.table("tickets")\
            .insert(nuevo_ticket)\
            .execute()
            
        if response.data and len(response.data) > 0:
            return response.data[0]
        raise Exception("No se retornaron datos tras la creación del ticket.")
    except Exception as e:
        error_msg = f"Error al crear el ticket de soporte: {str(e)}"
        print(error_msg)
        return {"error": error_msg}
