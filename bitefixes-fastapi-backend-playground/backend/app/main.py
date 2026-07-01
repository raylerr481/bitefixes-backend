import os
import logging
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv

# Importaciones locales
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

# Modelo sincronizado con el frontend
class ChatRequest(BaseModel):
    message: str
    user_id: str

# --- FUNCIONES ---
def guardar_mensaje(user_id: str, remitente: str, texto: str):
    try:
        supabase.table("historial_chats").insert({
            "user_id": user_id, "remitente": remitente, "mensaje": texto
        }).execute()
    except Exception as e:
        logger.error(f"Error en DB: {e}")

def obtener_historial(user_id: str) -> List[dict]:
    try:
        res = supabase.table("historial_chats").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
        return [{"sender": r["remitente"], "text": r["mensaje"]} for r in reversed(res.data)]
    except:
        return []

# --- ENDPOINTS ---
@app.get("/")
async def read_root():
    return {"status": "online"}

@app.post("/api/chat/direct")
async def chat_web(payload: ChatRequest):
    try:
        historial = obtener_historial(payload.user_id)
        resultado = procesar_con_bitey(payload.message, payload.user_id, historial)
        
        guardar_mensaje(payload.user_id, "user", payload.message)
        guardar_mensaje(payload.user_id, "bot", resultado["respuesta"])
        
        return {"reply": resultado["respuesta"]}
    except Exception as e:
        logger.error(f"Error procesando: {e}")
        return {"reply": "Lo siento, tuve un error técnico. Intenta de nuevo."}
