@app.get("/")
def read_root():
    return {"status": "BiteFixes is alive!"}
import os
import sys
import logging
import hashlib
import hmac
import httpx
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, Request, Response, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from dotenv import load_dotenv

# --- CORRECCIÓN DE RUTA PARA RENDER ---
# Asegura que el directorio que contiene la carpeta 'app' esté en el path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importaciones ahora corregidas
from app.database import supabase
from app.bitey_engine import procesar_con_bitey

# --- 1. CONFIGURACIÓN ---
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[RotatingFileHandler("bitefixes.log", maxBytes=1000000, backupCount=5), logging.StreamHandler()]
)
logger = logging.getLogger("BiteFixes")

app = FastAPI(title="BiteFixes Production API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables de entorno
APP_SECRET = os.getenv("APP_SECRET")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# --- 2. SEGURIDAD: Validación HMAC ---
async def validar_webhook_meta(request: Request, x_hub_signature_256: str = Header(None)):
    if not x_hub_signature_256:
        raise HTTPException(status_code=403, detail="Firma faltante")
    body = await request.body()
    hash_esperado = hmac.new(APP_SECRET.encode('utf-8'), msg=body, digestmod=hashlib.sha256).hexdigest()
    if f"sha256={hash_esperado}" != x_hub_signature_256:
        raise HTTPException(status_code=403, detail="Firma inválida")

# --- 3. PERSISTENCIA ---
def guardar_mensaje(user_id: str, remitente: str, texto: str):
    supabase.table("historial_chats").insert({
        "user_id": user_id, "remitente": remitente, "mensaje": texto
    }).execute()

def obtener_historial(user_id: str) -> List[Dict]:
    res = supabase.table("historial_chats").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
    return [{"sender": r["remitente"], "text": r["mensaje"]} for r in reversed(res.data)]

# --- 4. ENDPOINTS ---
@app.get("/health")
def health_check():
    return {"status": "online", "system": "BiteFixes Core"}

@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    if request.query_params.get("hub.mode") == "subscribe" and request.query_params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(request.query_params.get("hub.challenge"))
    raise HTTPException(status_code=403, detail="Token inválido")

@app.post("/webhook/whatsapp")
async def recibir_whatsapp(request: Request, firma: None = Depends(validar_webhook_meta)):
    body = await request.json()
    try:
        msg = body["entry"][0]["changes"][0]["value"]["messages"][0]
        numero = msg.get("from")
        texto = msg.get("text", {}).get("body", "").strip()
    except (KeyError, IndexError):
        return {"status": "ok"}

    guardar_mensaje(numero, "user", texto)
    historial = obtener_historial(numero)
    resultado = procesar_con_bitey(texto, numero, historial)
    
    respuesta_bot = resultado["respuesta"]
    guardar_mensaje(numero, "bot", respuesta_bot)
    await enviar_mensaje_whatsapp_api(numero, respuesta_bot)
    return {"status": "procesado"}

async def enviar_mensaje_whatsapp_api(to: str, text: str):
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}, headers=headers)
