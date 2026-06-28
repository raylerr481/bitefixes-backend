import { PythonFile } from '../types';

export const pythonFiles: PythonFile[] = [
  {
    name: 'database.py',
    path: 'app/database.py',
    description: 'Establece la conexión con Supabase Database y encapsula las operaciones CRUD para Clientes y Tickets de soporte.',
    language: 'python',
    content: `import os
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
        response = supabase.table("clientes")\\
            .select("id, nombre, whatsapp, direccion")\\
            .eq("whatsapp", clean_number)\\
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
        response = supabase.table("clientes")\\
            .insert(nuevo_cliente)\\
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
        response = supabase.table("tickets")\\
            .insert(nuevo_ticket)\\
            .execute()
            
        if response.data and len(response.data) > 0:
            return response.data[0]
        raise Exception("No se retornaron datos tras la creación del ticket.")
    except Exception as e:
        error_msg = f"Error al crear el ticket de soporte: {str(e)}"
        print(error_msg)
        return {"error": error_msg}
`
  },
  {
    name: 'tools.py',
    path: 'app/tools.py',
    description: 'Configura la SDK de Google Gen AI y define las herramientas (Function Calling) que el modelo de IA puede invocar.',
    language: 'python',
    content: `import os
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
   - Al inicio del chat, debes obtener el número de WhatsApp del usuario (el sistema te lo proveerá en el contexto) y llamar inmediatamente a la herramienta \`tool_verificar_cliente\` para saber si es un cliente registrado.
   - Si la herramienta te responde que está "registrado", dale la bienvenida usando su nombre (ejemplo: "¡Hola Juan! Qué gusto saludarte de nuevo...") y pregúntale en qué le puedes asistir hoy.
   - Si la herramienta te responde "no_registrado", indícale de manera muy amable que para brindarle asistencia técnica personalizada y agendar una visita primero necesitas darlo de alta en nuestro sistema. Solicítale amablemente de manera conversacional y fluida:
     a) Su nombre completo.
     b) Su dirección física para servicios de soporte en sitio.
   - Una vez que te provea estos datos de forma natural (puedes solicitarlos uno a uno si es mejor), llama a la herramienta \`tool_registrar_cliente\` para darlo de alta antes de continuar.

3. PROTOCOLO DE CATEGORIZACIÓN Y CREACIÓN DE TICKETS:
   - Cuando el cliente te describa su problema (ejemplo: "Mi PC no enciende", "No tengo internet", "Quiero instalar un programa"), analiza la descripción y clasifica el problema en una de las siguientes categorías válidas:
     * 'Hardware' (para laptops, computadoras lentas que no prenden, piezas dañadas, pantallas, etc.)
     * 'Software' (instalación de programas, virus, formateo, sistemas operativos)
     * 'Redes' (módem fallando, wifi sin señal, cableado estructurado)
     * 'Comercial' (cotizaciones, compra de licencias, contratos de soporte corporativo)
     * 'Otro' (cualquier problema que no encaje en las anteriores)
   - Una vez identificada la categoría y recopilada una breve descripción comprensible del problema, llama a la herramienta \`tool_crear_ticket\`.
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
`
  },
  {
    name: 'main.py',
    path: 'app/main.py',
    description: 'Punto de entrada de FastAPI. Expone el Webhook para recibir mensajes de WhatsApp Meta y API para Sitio Web o App Móvil.',
    language: 'python',
    content: `import os
from fastapi import FastAPI, Request, Response, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv

# Importar lógica del agente inteligente
from app.tools import ejecutar_agente_bitefixes

load_dotenv()

app = FastAPI(
    title="BiteFixes Omnichannel API",
    version="1.0.0",
    description="Servidor Backend de Producción para Chatbot WhatsApp, Web y App Móvil de BiteFixes con IA integrada."
)

# Configuración de CORS para permitir consumo desde Sitio Web y Apps Móviles híbridas (React Native, Flutter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustar a dominios específicos de producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Credenciales de WhatsApp Business provistas por Meta
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

# Base de datos local en memoria temporal para simular el historial de conversación.
# En producción, se recomienda almacenar esta sesión en Redis con un TTL (Time-to-Live)
# o directamente en una tabla de 'chats_historial' en Supabase para persistencia multicanal.
SESIONES_CHAT_TEMP: Dict[str, List[Dict[str, Any]]] = {}

# Esquemas de datos para endpoints de Consumo Web / Móvil directo
class MensajeDirectoPayload(BaseModel):
    usuario_id: str  # Puede ser el número de celular o un UUID
    mensaje: str
    canal: str = "web"  # "web" | "movil"

class RespuestaDirecta(BaseModel):
    respuesta: str
    tools_ejecutados: List[Dict[str, Any]]

# ---------------------------------------------------------------------------
# ENDPOINT DE SALUD (Health Check)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Mantenimiento"])
def health_check():
    return {
        "status": "online",
        "company": "BiteFixes",
        "services": {
            "fastapi": "running",
            "gemini_agent": "ready"
        }
    }

# ---------------------------------------------------------------------------
# WEBHOOK DE WHATSAPP: VERIFICACIÓN (Meta solicita un apretón de manos GET)
# ---------------------------------------------------------------------------
@app.get("/webhook/whatsapp", tags=["WhatsApp Webhook"])
def verificar_webhook_whatsapp(
    mode: Optional[str] = Query(None, alias="hub.mode"),
    token: Optional[str] = Query(None, alias="hub.verify_token"),
    challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """
    Verifica el webhook de WhatsApp Cloud API utilizando el token de verificación configurado en la consola de Meta.
    """
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        print("Webhook verificado exitosamente con Meta.")
        return Response(content=challenge, media_type="text/plain")
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fallo en la verificación del token de WhatsApp."
        )

# ---------------------------------------------------------------------------
# WEBHOOK DE WHATSAPP: RECEPCIÓN Y RESPUESTA (POST)
# ---------------------------------------------------------------------------
@app.post("/webhook/whatsapp", tags=["WhatsApp Webhook"])
async def recibir_mensaje_whatsapp(request: Request):
    """
    Recibe las notificaciones de eventos (mensajes entrantes) de WhatsApp Cloud API,
    los procesa utilizando el Agente Inteligente BiteFixes y responde al usuario.
    """
    body = await request.json()
    print("Notificación de WhatsApp recibida:", body)

    # Validar estructura estándar de mensajes de Meta
    if not (body.get("object") == "whatsapp_business_account" and "entry" in body):
         return {"status": "ignorado", "reason": "No es un evento de cuenta de WhatsApp"}

    try:
        entry = body["entry"][0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            # Puede ser una actualización de entrega de mensaje (delivered/read status), no requerimos responder
            return {"status": "ok", "detail": "Actualización de estado sin mensaje entrante."}

        # Extraer remitente y texto del mensaje
        message_data = messages[0]
        numero_whatsapp = message_data.get("from")  # Ejemplo: '5215512345678'
        message_type = message_data.get("type")

        if message_type != "text":
            # Si el usuario envía audios, fotos o archivos, solicitamos que use texto
            # En producción se puede usar Gemini Multimodal para procesar fotos de equipos dañados
            await enviar_mensaje_whatsapp_api(
                numero_whatsapp,
                "¡Hola! Por el momento solo puedo procesar mensajes de texto. Por favor descríbeme tu problema por escrito para poder ayudarte a registrar tu ticket."
            )
            return {"status": "ok", "detail": "Mensaje no-texto manejado de forma genérica."}

        texto_usuario = message_data.get("text", {}).get("body", "").strip()
        print(f"Mensaje de {numero_whatsapp}: '{texto_usuario}'")

        # Inicializar historial de conversación en memoria si no existe
        if numero_whatsapp not in SESIONES_CHAT_TEMP:
            SESIONES_CHAT_TEMP[numero_whatsapp] = []

        historial = SESIONES_CHAT_TEMP[numero_whatsapp]

        # Ejecutar el agente experto BiteFixes (que incluye el Function Calling integrado en tools.py)
        resultado_agente = ejecutar_agente_bitefixes(
            mensaje_usuario=texto_usuario,
            numero_whatsapp=numero_whatsapp,
            historial_conversacion=historial
        )

        respuesta_bot = resultado_agente["respuesta"]

        # Actualizar historial del usuario (máximo 15 mensajes para optimización de tokens y memoria)
        historial.append({"sender": "user", "text": texto_usuario})
        historial.append({"sender": "bot", "text": respuesta_bot})
        if len(historial) > 15:
            SESIONES_CHAT_TEMP[numero_whatsapp] = historial[-15:]

        # Enviar la respuesta del Bot de vuelta al cliente mediante la API de Meta Graph
        await enviar_mensaje_whatsapp_api(numero_whatsapp, respuesta_bot)

        return {
            "status": "procesado",
            "destinatario": numero_whatsapp,
            "respuesta_generada": respuesta_bot,
            "tools_ejecutados": resultado_agente["tools_ejecutados"]
        }

    except Exception as e:
        print(f"Error crítico procesando webhook de WhatsApp: {str(e)}")
        # Siempre responder con estatus 200 a Meta para evitar reintentos infinitos que saturen el backend
        return {"status": "error_interno", "detail": str(e)}

# ---------------------------------------------------------------------------
# ENDPOINT DE CONSUMO OMNICANAL DIRECTO (Sitio Web y App Móvil)
# ---------------------------------------------------------------------------
@app.post("/api/chat/direct", response_model=RespuestaDirecta, tags=["Canal Digital (Web/App)"])
def chat_directo(payload: MensajeDirectoPayload):
    """
    Permite interactuar con el mismo cerebro e historial de BiteFixes desde la 
    sección de Soporte Técnico en el Sitio Web o desde la App Móvil nativa.
    """
    usuario_id = payload.usuario_id
    mensaje = payload.mensaje

    if usuario_id not in SESIONES_CHAT_TEMP:
        SESIONES_CHAT_TEMP[usuario_id] = []

    historial = SESIONES_CHAT_TEMP[usuario_id]

    # Ejecutar mismo agente omnicanal
    resultado = ejecutar_agente_bitefixes(
        mensaje_usuario=mensaje,
        numero_whatsapp=usuario_id, # En web puede ser el celular ingresado o identificador del perfil
        historial_conversacion=historial
    )

    respuesta_bot = resultado["respuesta"]

    # Registrar historial
    historial.append({"sender": "user", "text": mensaje})
    historial.append({"sender": "bot", "text": respuesta_bot})
    if len(historial) > 20:
        SESIONES_CHAT_TEMP[usuario_id] = historial[-20:]

    return RespuestaDirecta(
        respuesta=respuesta_bot,
        tools_ejecutados=resultado["tools_ejecutados"]
    )

# ---------------------------------------------------------------------------
# UTILIDAD: ENVIAR MENSAJE VIA METAGRAPH WHATSAPP CLOUD API
# ---------------------------------------------------------------------------
async def enviar_mensaje_whatsapp_api(numero_destino: str, texto_mensaje: str):
    """
    Envía un mensaje de texto de salida al usuario final utilizando el endpoint
    oficial de WhatsApp Cloud API de Meta.
    """
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        print("ADVERTENCIA: API de WhatsApp no configurada. Mensaje simulado de salida:")
        print(f"Hacia {numero_destino}: {texto_mensaje}")
        return

    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {
            "body": texto_mensaje
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                print(f"Fallo al enviar mensaje por API de WhatsApp: {response.status_code} - {response.text}")
            else:
                print(f"Mensaje enviado exitosamente a {numero_destino}")
        except Exception as e:
            print(f"Excepción de conexión enviando mensaje de WhatsApp: {str(e)}")

# Correr con: uvicorn app.main:app --reload --port 3000
`
  },
  {
    name: '.env.example',
    path: '.env.example',
    description: 'Variables de entorno obligatorias para el funcionamiento del backend de BiteFixes.',
    language: 'ini',
    content: `# LLAVE API DE GOOGLE GEMINI (Obtenida desde Google AI Studio)
GEMINI_API_KEY="AIzaSyYourGeminiApiKeyHere..."

# CONFIGURACIÓN DEL CLIENTE DE SUPABASE (Conexión base de datos)
SUPABASE_URL="https://yourprojectid.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.yourKey..."

# CONFIGURACIÓN DE METAPLATFORM - WHATSAPP BUSINESS CLOUD API
WHATSAPP_PHONE_NUMBER_ID="your_phone_number_id_from_meta"
WHATSAPP_TOKEN="EAAGyour_long_lived_user_token_from_meta"
WHATSAPP_VERIFY_TOKEN="bitefixes_webhook_security_token_random_123"

# AMBIENTE DEL SERVIDOR
PORT=3000
ENVIRONMENT="production" # "development" | "production"
`
  },
  {
    name: 'requirements.txt',
    path: 'requirements.txt',
    description: 'Lista de dependencias y librerías de Python requeridas para correr la aplicación en producción.',
    language: 'text',
    content: `fastapi==0.111.0
uvicorn==0.30.1
supabase==2.5.1
google-genai==0.2.1
python-dotenv==1.0.1
pydantic==2.7.4
httpx==0.27.0
`
  },
  {
    name: 'schema.sql',
    path: 'schema.sql',
    description: 'Estructura de la base de datos de Supabase. SQL listo para ejecutar en el SQL Editor de tu proyecto.',
    language: 'sql',
    content: `-- ------------------------------------------------------------
-- Base de Datos para Sistema de Soporte Técnico 'BiteFixes'
-- Ejecuta este script en la consola de SQL de Supabase
-- ------------------------------------------------------------

-- Habilitar extensión para generar UUIDs de manera nativa si es necesario
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. TABLA DE CLIENTES
CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(150) NOT NULL,
    whatsapp VARCHAR(20) UNIQUE NOT NULL, -- Almacena números limpios ej: '34612345678'
    direccion TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índice para búsquedas ultra rápidas por número de whatsapp (indispensable para el webhook)
CREATE INDEX IF NOT EXISTS idx_clientes_whatsapp ON clientes(whatsapp);

-- 2. TABLA DE TICKETS DE SOPORTE
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY, -- Números secuenciales legibles e ideales para tickets de clientes (ej: Ticket #1003)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    categoria VARCHAR(30) NOT NULL CHECK (categoria IN ('Hardware', 'Software', 'Redes', 'Comercial', 'Otro')),
    cliente_id UUID REFERENCES clientes(id) ON DELETE CASCADE NOT NULL,
    descripcion TEXT NOT NULL,
    estatus VARCHAR(20) NOT NULL DEFAULT 'Abierto' CHECK (estatus IN ('Abierto', 'En Proceso', 'Resuelto'))
);

-- Insertar Datos Demo Iniciales para Pruebas
INSERT INTO clientes (nombre, whatsapp, direccion) 
VALUES 
('Carlos Mendoza', '34612345678', 'Calle Gran Vía 45, Piso 3, Madrid'),
('María Fernández', '34698765432', 'Avenida Diagonal 120, Barcelona')
ON CONFLICT (whatsapp) DO NOTHING;

INSERT INTO tickets (categoria, cliente_id, descripcion, estatus)
SELECT 
    'Hardware', 
    id, 
    'Mi computadora portátil enciende pero la pantalla se queda completamente en negro.', 
    'Abierto'
FROM clientes 
WHERE whatsapp = '34612345678'
LIMIT 1;

INSERT INTO tickets (categoria, cliente_id, descripcion, estatus)
SELECT 
    'Redes', 
    id, 
    'El enrutador de oficina pierde conexión intermitentemente cada tarde a las 3 PM.', 
    'En Proceso'
FROM clientes 
WHERE whatsapp = '34698765432'
LIMIT 1;
`
  },
  {
    name: 'README.md',
    path: 'README.md',
    description: 'Guía detallada de arquitectura, despliegue y puesta en marcha del proyecto backend para BiteFixes.',
    language: 'markdown',
    content: `# Backend Omnicanal de Soporte Técnico - BiteFixes 🛠️🤖

Este repositorio contiene la estructura completa, modular y documentada del backend de producción para **BiteFixes**. Diseñado con una arquitectura de microservicios limpia, utiliza **FastAPI** como pasarela API robusta, **Supabase (PostgreSQL)** para persistencia transaccional rápida y el modelo **Gemini 3.5 Flash** de Google con **Function Calling** nativo para resolver conversaciones y automatizar operaciones de soporte técnico en tiempo real.

---

## 🏗️ Arquitectura Omnicanal de Flujo
\`\`\`text
[ WhatsApp Chatbot (Meta) ] ──┐
[ Canal Web (Widget Chat)   ] ──┼─► [ FastAPI backend ] ──► [ Gemini 3.5 Flash ] (Decide herram.)
[ App Móvil (Soporte App)   ] ──┘         │                             │ (Function Calls)
                                          ▼                             ▼
                              [ Supabase database ] ◄───────────────────┘
                                - 'clientes' table
                                - 'tickets' table
\`\`\`

---

## ⚡ Requisitos Previos

- **Python 3.10 o superior** instalado.
- Un proyecto activo en **Supabase** (puedes crear uno gratuito en [supabase.com](https://supabase.com)).
- Una llave de API de **Google Gemini** (puedes generarla gratis en [Google AI Studio](https://ai.studio)).
- Una cuenta de **Facebook Developer** con el producto **WhatsApp Business API** activado si deseas conectar el bot de WhatsApp real.

---

## 🚀 Despliegue y Puesta en Marcha Local

### 1. Clonar el proyecto y acceder al directorio
\`\`\`bash
mkdir bitefixes-backend && cd bitefixes-backend
# Copia los archivos del hub en su respectiva estructura
\`\`\`

### 2. Configurar el Entorno Virtual
Crea un entorno de ejecución aislado para evitar conflictos de dependencias en tu máquina:
\`\`\`bash
python -m venv venv

# Activar en Windows:
venv\\Scripts\\activate

# Activar en Linux / macOS:
source venv/bin/activate
\`\`\`

### 3. Instalar Dependencias Requeridas
Instala los módulos del archivo \`requirements.txt\`:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. Inicializar la Base de Datos en Supabase
1. Ingresa a la consola de administración de tu proyecto en Supabase.
2. Abre la sección de **SQL Editor** y crea una nueva consulta.
3. Copia e ingresa todo el contenido del archivo \`schema.sql\` provisto en este hub.
4. Presiona **Run** para crear de inmediato las tablas de \`clientes\` y \`tickets\`, junto a los índices de búsqueda y datos demo para pruebas iniciales.

### 5. Configurar Variables de Entorno
Crea un archivo llamado \`.env\` en la raíz del proyecto basándote en \`.env.example\`:
\`\`\`bash
cp .env.example .env
# Abre .env y edita las llaves de Supabase, Gemini y WhatsApp Business.
\`\`\`

### 6. Ejecutar el Servidor de Desarrollo
Corre el servidor utilizando **Uvicorn**:
\`\`\`bash
uvicorn app.main:app --reload --port 3000
\`\`\`
El servidor estará activo de inmediato en: \`http://localhost:3000\`

---

## 🔗 Pruebas de Endpoints e Integración

### Documentación Interactiva de la API
FastAPI genera de forma automática documentación de producción interactiva bajo estándares de OpenAPI:
- **Swagger UI**: Accede a \`http://localhost:3000/docs\` para interactuar visualmente con los endpoints, simular requests y ver payloads de respuesta detallados.
- **Redoc**: Accede a \`http://localhost:3000/redoc\` para una lectura formal de especificaciones técnicas.

---

## 💬 Flujo Conversacional del Bot (Paso a Paso)

El bot está diseñado para guiar de manera inteligente al cliente sin que este se dé cuenta del flujo técnico subyacente:

1. **Recepción**: Llega el mensaje al webhook de WhatsApp con el número del cliente.
2. **Identificación**: Gemini recibe el contexto y solicita de inmediato la herramienta \`tool_verificar_cliente\`.
3. **Registro (Si es necesario)**:
   - Si no está registrado en Supabase, el bot le solicita su nombre y dirección de forma cordial.
   - Al recibir los datos, se llama a \`tool_registrar_cliente\`, guardándolos permanentemente en Supabase.
4. **Análisis del Problema**: El bot escucha la avería, la categoriza lógicamente (\`Hardware\`, \`Software\`, \`Redes\`, etc.), y llama a \`tool_crear_ticket\` para levantar el reporte de inmediato.
5. **Confirmación**: Se le entrega al cliente su número oficial de ticket para su tranquilidad, cerrando la interacción de manera profesional.
`
  }
];
