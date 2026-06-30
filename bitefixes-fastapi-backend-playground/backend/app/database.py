import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Usamos variables de entorno (más seguro que hardcodearlas)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan configurar las variables de entorno SUPABASE_URL y/o SUPABASE_KEY.")

# --- AQUÍ ESTÁ LA CLAVE: Definimos el cliente globalmente ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def verificar_cliente_por_whatsapp(numero_whatsapp: str) -> Optional[Dict[str, Any]]:
    # Ahora usamos la variable global 'supabase'
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
        return None

def registrar_cliente_nuevo(nombre: str, whatsapp: str, direccion: str) -> Dict[str, Any]:
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
        return {"error": str(e)}

def crear_ticket_soporte(cliente_id: str, categoria: str, descripcion: str) -> Dict[str, Any]:
    categorias_validas = ["Hardware", "Software", "Redes", "Comercial", "Otro"]
    categoria = categoria if categoria in categorias_validas else "Otro"
        
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
        return {"error": str(e)}
