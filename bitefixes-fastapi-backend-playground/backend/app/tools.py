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
    """Verifica si un número de WhatsApp pertenece a un cliente registrado."""
    cliente = verificar_cliente_por_whatsapp(numero_whatsapp)
    if cliente:
        return json.dumps({"status": "registrado", "cliente": cliente})
    return json.dumps({"status": "no_registrado", "mensaje": "No registrado."})

def tool_registrar_cliente(nombre: str, whatsapp: str, direccion: str) -> str:
    """Registra un cliente nuevo en el sistema de BiteFixes."""
    resultado = registrar_cliente_nuevo(nombre, whatsapp, direccion)
    return json.dumps(resultado)

def tool_crear_ticket(cliente_id: str, categoria: str, descripcion: str) -> str:
    """Crea un ticket de soporte técnico en el sistema de BiteFixes."""
    resultado = crear_ticket_soporte(cliente_id, categoria, descripcion)
    return json.dumps(resultado)

# Mapeo de herramientas para ejecución dinámica
HERRAMIENTAS_MAPA: Dict[str, Callable] = {
    "tool_verificar_cliente": tool_verificar_cliente,
    "tool_registrar_cliente": tool_registrar_cliente,
    "tool_crear_ticket": tool_crear_ticket
}

# ---------------------------------------------------------------------------
# COMPORTAMIENTO Y PROMPT DEL SISTEMA (Línea limpia para evitar errores de copia)
# ---------------------------------------------------------------------------

INSTRUCCIONES_SISTEMA = "Eres Bitey, el asistente de soporte tecnico oficial de BiteFixes. Tu objetivo es saludar al usuario, usar tool_verificar_cliente con su numero de whatsapp para verificarlo. Si no esta registrado, pidele amablemente su nombre y direccion y registralo con tool_registrar_cliente. Si ya esta registrado o despues de registrarlo, pidele la descripcion de su problema y crea un ticket con tool_crear_ticket clasificandolo en Hardware, Software, Redes, Comercial u Otro. Responde de forma breve y amable."

def ejecutar_agente_bitefixes(mensaje_usuario: str, numero_whatsapp: str, historial_conversacion: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Envía el mensaje al modelo Gemini y procesa la llamada a funciones."""
    # Configurar herramientas y directivas
    config = types.GenerateContentConfig(
        system_instruction=INSTRUCCIONES_SISTEMA,
        temperature=0.3,
        tools=[
            types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name="tool_verificar_cliente",
                    description="Verifica si un número de WhatsApp pertenece a un cliente registrado en BiteFixes.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "numero_whatsapp": types.Schema(type="STRING", description="El número de teléfono con código de país.")
                        },
                        required=["numero_whatsapp"]
                    )
                ),
                types.FunctionDeclaration(
                    name="tool_registrar_cliente",
                    description="Registra un cliente nuevo en el sistema de BiteFixes.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "nombre": types.Schema(type="STRING", description="Nombre completo del cliente."),
                            "whatsapp": types.Schema(type="STRING", description="Número de teléfono/WhatsApp del cliente."),
                            "direccion": types.Schema(type="STRING", description="Dirección física para servicio técnico.")
                        },
                        required=["nombre", "whatsapp", "direccion"]
                    )
                ),
                types.FunctionDeclaration(
                    name="tool_crear_ticket",
                    description="Crea un ticket de soporte técnico en el sistema de BiteFixes.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "cliente_id": types.Schema(type="STRING", description="El ID del cliente registrado."),
                            "categoria": types.Schema(
                                type="STRING", 
                                description="Categoría del ticket: Hardware, Software, Redes, Comercial, Otro."
                            ),
                            "descripcion": types.Schema(type="STRING", description="Descripción detallada de la falla.")
                        },
                        required=["cliente_id", "categoria", "descripcion"]
                    )
                )
            ])
        ]
    )

    # Convertir el historial al formato compatible con Google Gen AI (Contents)
    contents = []
    for chat in historial_conversacion:
        role = "user" if chat["sender"] == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part.from_text(text=chat["text"])]
        ))
        
    # Añadir el mensaje actual
    contexto_mensaje = f"[WhatsApp Remitente: {numero_whatsapp}] {mensaje_usuario}"
    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=contexto_mensaje)]
    ))

    # Realizar llamada al modelo usando la versión oficial estable
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=config
    )

    respuesta_texto = response.text or ""
    tool_calls_ejecutadas = []

    # Validar si el modelo solicitó llamadas a funciones (Function Calling)
    if response.function_calls:
        for call in response.function_calls:
            nombre_tool = call.name
            args = call.args
            
            tool_calls_ejecutadas.append({
                "nombre": nombre_tool,
                "argumentos": args
            })
            
            if nombre_tool in HERRAMIENTAS_MAPA:
                funcion_local = HERRAMIENTAS_MAPA[nombre_tool]
                
                try:
                    resultado_tool_str = funcion_local(**args)
                    resultado_dict = json.loads(resultado_tool_str)
                    
                    part_call = types.Part.from_function_call(name=call.name, args=call.args)
                    part_resp = types.Part.from_function_response(name=call.name, response={"result": resultado_dict})
                    
                    contents.append(types.Content(role="model", parts=[part_call]))
                    contents.append(types.Content(role="user", parts=[part_resp]))
                    
                    final_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=contents,
                        config=config
                    )
                    respuesta_texto = final_response.text or ""
                    
                except Exception as e:
                    print(f"Error al ejecutar la herramienta {nombre_tool}: {str(e)}")
                    respuesta_texto = "Lo lamento, hubo un inconveniente técnico al procesar la solicitud."

    return {
        "respuesta": respuesta_texto,
        "tools_ejecutados": tool_calls_ejecutadas
    }
