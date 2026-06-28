import os
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

        # Para depuración/ejecución con el Agente de BiteFixes
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
