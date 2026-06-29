import os
import json
from typing import List, Dict, Any, Callable
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Importar funciones de base de datos
from app.database import (
    verificar_cliente_por_whatsapp,
    registrar_cliente_nuevo,
    crear_ticket_soporte
)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("Falta configurar la variable de entorno GEMINI_API_KEY.")

# Inicializar cliente de Google Gen AI con el SDK oficial actual
client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------------------------------------------------------
# DEFINICIÓN DE HERRAMIENTAS (Docstrings y Type Hints)
# ---------------------------------------------------------------------------

def tool_verificar_cliente(numero_whatsapp: str) -> str:
    """
    Verifica si un número de WhatsApp pertenece a un cliente registrado en BiteFixes.
    
    Args:
        numero_whatsapp: El número telefónico con código de país, ejemplo: '+525512345678'
        
    Returns:
        Un JSON string con los datos del cliente si existe, o un estado 'no_registrado'.
    """
    cliente = verificar_cliente_por_whatsapp(numero_whatsapp)
    if cliente:
        return json.dumps({"status": "registrado", "cliente": cliente})
    return json.dumps({"status": "no_registrado", "mensaje": "El número de WhatsApp no pertenece a un cliente registrado."})

def tool_registrar_cliente(nombre: str, whatsapp: str, direccion: str) -> str:
    """
    Registra un cliente nuevo en el sistema de BiteFixes con su nombre, whatsapp y dirección física.
    
    Args:
        nombre: Nombre completo del cliente, ejemplo: 'Carlos Mendoza'
        whatsapp: Número de teléfono/WhatsApp, ejemplo: '+525512345678'
        direccion: Dirección física donde requiere el servicio técnico, ejemplo: 'Av. Reforma 123, CDMX'
        
    Returns:
        Un JSON string con la información del cliente registrado o un mensaje de error.
    """
    resultado = registrar_cliente_nuevo(nombre, whatsapp, direccion)
    return json.dumps(resultado)

def tool_crear_ticket(cliente_id: str, categoria: str, descripcion: str) -> str:
    """
    Crea un ticket de soporte técnico en el sistema de BiteFixes.
    
    Args:
        cliente_id: El ID único del cliente registrado (UUID o entero como cadena).
        categoria: La categoría del problema. Debe ser una de: 'Hardware', 'Software', 'Redes', 'Comercial', 'Otro'.
        descripcion: Detalle del problema de soporte que presenta el cliente.
        
    Returns:
        Un JSON string con los detalles del ticket creado, incluyendo su número de ticket y estatus inicial.
    """
    resultado = crear_ticket_soporte(cliente_id, categoria, descripcion)
    return json.dumps(resultado)

# Mapeo de herramientas para ejecución dinámica
HERRAMIENTAS_MAPA: Dict[str, Callable] = {
    "tool_verificar_cliente": tool_verificar_cliente,
    "tool_registrar_cliente": tool_registrar_cliente,
    "tool_crear_ticket": tool_crear_ticket
}

# ---------------------------------------------------------------------------
# COMPORTAMIENTO Y PROMPT DEL SISTEMA (System Instructions)
# ---------------------------------------------------------------------------

INSTRUCCIONES_SISTEMA = """
Eres "Bitey", el Asistente Inteligente oficial de BiteFixes, una empresa líder en soporte técnico a domicilio y servicios digitales (Hardware, Software, Redes, y Consultoría Comercial). Tu misión es resolver solicitudes de clientes y registrar tickets de soporte técnico de forma empática, profesional y muy eficiente.

Sigue rigurosamente este protocolo de atención al usuario:

1. COMPORTAMIENTO GENERAL:
   - Saluda cordialmente y con entusiasmo ("¡Hola! Soy Bitey de BiteFixes...").
   - Habla en español de manera natural, clara y empática. Eres un experto técnico, pero
