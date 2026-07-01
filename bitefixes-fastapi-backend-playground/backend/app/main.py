import os
import sys
import logging
import hashlib
import hmac
import httpx
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

# --- RUTA ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import supabase
from app.bitey_engine import procesar_con_bitey

# --- CONFIGURACIÓN ---
load_dotenv()
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
logger = logging.getLogger("BiteFixes")

app = FastAPI(title="BiteFixes Production API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para validar datos
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "web_user"

# Variables
APP_SECRET = os.getenv("APP_SECRET")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# --- FUNCIONES ---
def guardar_mensaje(user_id: str, remitente: str, texto: str):
    try:
        supabase.table("historial_chats").insert({
            "user_id": user_id, "remitente": remitente, "mensaje": texto
        }).execute()
    except Exception as e:
        logger.error(f"Error guardando en Supabase: {e}")

def obtener_historial(user_id: str) -> List[dict]:
    res = supabase.table("historial_chats").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
    return [{"sender": r["remitente"], "text": r["mensaje"]} for r in reversed(res.data)]

# --- ENDPOINTS ---

@app.post("/api/chat/direct")
async def chat_web(payload: ChatRequest):
    try:
        historial = obtener_historial(payload.user_id)
        resultado = procesar_con_bitey(payload.message, payload.user_id, historial)
        
        guardar_mensaje(payload.user_id, "user", payload.message)
        guardar_mensaje(payload.user_id, "bot", resultado["respuesta"])
        
        return {"reply": resultado["respuesta"]}
    except Exception as e:
        logger.error(f"Error en motor: {e}")
        # Retornar JSON incluso en error para evitar el error de sintaxis en el frontend
        return {"reply": "Lo siento, tuve un error procesando tu mensaje. Intenta de nuevo."}

@app.get("/webhook/whatsapp")
async def verify_webhook(hub_mode: str = Header(None, alias="hub.mode"), 
                         hub_token: str = Header(None, alias="hub.verify_token"),
                         hub_challenge: int = Header(None, alias="hub.challenge")):
    if hub_mode == "subscribe" and hub_token == VERIFY_TOKEN:
        return hub_challenge
    raise HTTPException(status_code=403, detail="Token inválido")

@app.post("/webhook/whatsapp")
async def recibir_whatsapp(request: Request):
    # Lógica simplificada para evitar errores de tipo si la estructura cambia
    body = await request.json()
    return {"status": "ok"}
