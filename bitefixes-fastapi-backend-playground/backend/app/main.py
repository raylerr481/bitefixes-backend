import os
import logging
import hashlib
import hmac
import httpx
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, Request, Response, HTTPException, Query, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
load_dotenv()

# Logger estructurado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[RotatingFileHandler("bitefixes.log", maxBytes=1000000, backupCount=5), logging.StreamHandler()]
)
logger = logging.getLogger("BiteFixes")

app = FastAPI(title="BiteFixes Production API", version="1.0.0")

# Cliente Supabase
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Credenciales Meta
APP_SECRET = os.getenv("APP_SECRET")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

# --- 2. SEGURIDAD: Validación HMAC ---
async def validar_webhook_meta(request: Request, x_hub_signature_256: str = Header(None)):
    if not x_hub_signature_256:
        raise HTTPException(status_code=403, detail="Firma faltante")
    body = await request.body()
    hash_esperado = hmac.new(APP_SECRET.encode('utf-8'), msg=body, digestmod=hashlib.sha256).hexdigest()
    if f"sha256={hash_esperado}" != x_hub_signature_256:
        raise HTTPException(status_code=403, detail="Firma inválida")

# --- 3. PERSISTENCIA: Funciones Supabase ---
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

@app.post("/webhook/whatsapp", tags=["WhatsApp"])
async def recibir_whatsapp(request: Request, firma: None = Depends(validar_webhook_meta)):
    body = await request.json()
    
    # Manejo de mensaje
    message_data = body["entry"][0]["changes"][0]["value"].get("messages", [])
    if not message_data: return {"status": "ok"}
    
    numero_whatsapp = message_data[0].get("from")
    texto_usuario = message_data[0].get("text", {}).get("body", "").strip()

    # Persistir entrada
    guardar_mensaje(numero_whatsapp, "user", texto_usuario)
    
    # Obtener historial y procesar con agente
    historial = obtener_historial(numero_whatsapp)
    from app.tools import ejecutar_agente_bitefixes # Asegúrate de que este import sea correcto
    resultado = ejecutar_agente_bitefixes(texto_usuario, numero_whatsapp, historial)
    
    # Persistir salida
    guardar_mensaje(numero_whatsapp, "bot", resultado["respuesta"])
    
    # Enviar respuesta a Meta
    await enviar_mensaje_whatsapp_api(numero_whatsapp, resultado["respuesta"])
    
    return {"status": "procesado"}

async def enviar_mensaje_whatsapp_api(to: str, text: str):
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}, headers=headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
