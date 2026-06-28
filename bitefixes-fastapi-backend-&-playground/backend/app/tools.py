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
# El SDK de google-genai inspecciona las firmas de las funciones y sus docstrings
# para generar automáticamente la especificación OpenAPI que el modelo comprende.
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
# Define la personalidad, límites, y flujo resolutivo del asistente de soporte.
# ---------------------------------------------------------------------------

INSTRUCCIONES_SISTEMA = """
Eres "Bitey", el Asistente Inteligente oficial de BiteFixes, una empresa líder en soporte técnico a domicilio y servicios digitales (Hardware, Software, Redes, y Consultoría Comercial). Tu misión es resolver solicitudes de clientes y registrar tickets de soporte técnico de forma empática, profesional y muy eficiente.

Sigue rigurosamente este protocolo de atención al usuario:

1. COMPORTAMIENTO GENERAL:
   - Saluda cordialmente y con entusiasmo ("¡Hola! Soy Bitey de BiteFixes...").
   - Habla en español de manera natural, clara y empática. Eres un experto técnico, pero hablas con un lenguaje accesible y sin jerga innecesaria que pueda confundir al cliente.
   - Mantén tus respuestas breves y concisas, óptimas para mensajería como WhatsApp (párrafos cortos, uso estratégico de negritas y emojis).

2. PROTOCOLO DE IDENTIFICACIÓN DE CLIENTES (Paso indispensable antes de crear tickets):
   - Al inicio del chat, debes obtener el número de WhatsApp del usuario (el sistema te lo proveerá en el contexto) y llamar inmediatamente a la herramienta `tool_verificar_cliente` para saber si es un cliente registrado.
   - Si la herramienta te responde que está "registrado", dale la bienvenida usando su nombre (ejemplo: "¡Hola Juan! Qué gusto saludarte de nuevo...") y pregúntale en qué le puedes asistir hoy.
   - Si la herramienta te responde "no_registrado", indícale de manera muy amable que para brindarle asistencia técnica personalizada y agendar una visita primero necesitas darlo de alta en nuestro sistema. Solicítale amablemente de manera conversacional y fluida:
     a) Su nombre completo.
     b) Su dirección física para servicios de soporte en sitio.
   - Una vez que te provea estos datos de forma natural (puedes solicitarlos uno a uno si es mejor), llama a la herramienta `tool_registrar_cliente` para darlo de alta antes de continuar.

3. PROTOCOLO DE CATEGORIZACIÓN Y CREACIÓN DE TICKETS:
   - Cuando el cliente te describa su problema (ejemplo: "Mi PC no enciende", "No tengo internet", "Quiero instalar un programa"), analiza la descripción y clasifica el problema en una de las siguientes categorías válidas:
     * 'Hardware' (para laptops, computadoras lentas que no prenden, piezas dañadas, pantallas, etc.)
     * 'Software' (instalación de programas, virus, formateo, sistemas operativos)
     * 'Redes' (módem fallando, wifi sin señal, cableado estructurado)
     * 'Comercial' (cotizaciones, compra de licencias, contratos de soporte corporativo)
     * 'Otro' (cualquier problema que no encaje en las anteriores)
   - Una vez identificada la categoría y recopilada una breve descripción comprensible del problema, llama a la herramienta `tool_crear_ticket`.
   - Una vez que la herramienta te confirme que el ticket fue creado con éxito, confírmale alegremente los detalles al cliente: proporciónale el Número de Ticket de soporte que te devolvió la base de datos, la categoría asignada, el estatus ('Abierto') y dile que un técnico especializado de BiteFixes lo contactará de inmediato para coordinar la visita o iniciar la ayuda remota.

REGLAS DE SEGURIDAD IMPORTANTES:
- Solo puedes llamar a las herramientas provistas. No inventes ID de clientes, nombres o tickets.
- Si el cliente te pide hablar de temas fuera de soporte técnico, hardware, software o servicios de BiteFixes, redirígelo educadamente al foco de soporte de la empresa.
- Si te falta algún parámetro para registrar al cliente o crear el ticket, pídelo de forma clara y cordial antes de intentar ejecutar la herramienta.
"""

def ejecutar_agente_bitefixes(mensaje_usuario: str, numero_whatsapp: str, historial_conversacion: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Envía el mensaje del usuario al modelo Gemini con el historial actual, ejecuta
    cualquier llamada a función sugerida por el modelo en Supabase, y genera la respuesta final.
    """
    # Configurar herramientas y directivas
    config = types.GenerateContentConfig(
        system_instruction=INSTRUCCIONES_SISTEMA,
        temperature=0.3,  # Baja temperatura para consistencia técnica y precisión en Function Calling
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
        
    # Añadir el mensaje actual del usuario inyectando el número de WhatsApp como contexto adicional
    contexto_mensaje = f"[WhatsApp Remitente: {numero_whatsapp}] {mensaje_usuario}"
    contents.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=contexto_mensaje)]
    ))

    # Realizar llamada al modelo
    response = client.models.generate_content(
        model="gemini-3.5-flash",
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
            
            # Registrar ejecución del tool en logs
            tool_calls_ejecutadas.append({
                "nombre": nombre_tool,
                "argumentos": args
            })
            
            if nombre_tool in HERRAMIENTAS_MAPA:
                # Ejecutar la función local de base de datos correspondiente
                funcion_local = HERRAMIENTAS_MAPA[nombre_tool]
                
                try:
                    # Desempaquetar argumentos e invocar
                    resultado_tool_str = funcion_local(**args)
                    resultado_dict = json.loads(resultado_tool_str)
                    
                    # Añadir la llamada y el resultado al flujo para que Gemini los analice y dé respuesta final
                    part_call = types.Part.from_function_call(
                        name=call.name,
                        args=call.args
                    )
                    part_resp = types.Part.from_function_response(
                        name=call.name,
                        response={"result": resultado_dict}
                    )
                    
                    # Enviar la respuesta de la función de vuelta a Gemini para el mensaje conclusivo
                    contents.append(types.Content(role="model", parts=[part_call]))
                    contents.append(types.Content(role="user", parts=[part_resp]))
                    
                    final_response = client.models.generate_content(
                        model="gemini-3.5-flash",
                        contents=contents,
                        config=config # Mantenemos la configuración para guiar la respuesta del bot
                    )
                    respuesta_texto = final_response.text or ""
                    
                except Exception as e:
                    print(f"Error al ejecutar la herramienta {nombre_tool}: {str(e)}")
                    respuesta_texto = "Lo lamento, hubo un inconveniente técnico al procesar la solicitud en nuestro sistema. ¿Podrías intentar nuevamente?"

    return {
        "respuesta": respuesta_texto,
        "tools_ejecutados": tool_calls_ejecutadas
    }
