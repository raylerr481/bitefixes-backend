import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

# Importaciones locales
from app.database import supabase
from app.bitey_engine import procesar_con_bitey

# --- CONFIGURACIÓN ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BiteFixes")

# 1. Definición de la aplicación (Instancia única y principal)
app = FastAPI(title="BiteFixes Production API")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo estricto para validar el JSON que viene del frontend
class ChatRequest(BaseModel):
    message: str
    user_id: str

# --- FUNCIONES DE BASE DE DATOS ---
def guardar_mensaje(user_id: str, remitente: str, texto: str):
    try:
        supabase.table("historial_chats").insert({
            "user_id": user_id, 
            "remitente": remitente, 
            "mensaje": texto
        }).execute()
    except Exception as e:
        logger.error(f"Error guardando en Supabase: {e}")

def obtener_historial(user_id: str) -> List[dict]:
    try:
        res = supabase.table("historial_chats").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
        # Invertir para que el orden sea cronológico (viejo -> nuevo)
        return [{"sender": r["remitente"], "text": r["mensaje"]} for r in reversed(res.data)]
    except Exception as e:
        logger.warning(f"No se pudo obtener historial: {e}")
        return []

# --- ENDPOINTS ---
@app.get("/")
async def read_root():
    return {"status": "online"}

@app.post("/api/chat/direct")
async def chat_web(payload: ChatRequest):
    # Log de diagnóstico
    logger.info(f"Procesando mensaje de: {payload.user_id}")
    
    try:
        # 1. Obtener contexto
        historial = obtener_historial(payload.user_id)
        
        # 2. Procesar con el motor
        resultado = procesar_con_bitey(payload.message, payload.user_id, historial)
        
        # 3. Guardar interacción
        guardar_mensaje(payload.user_id, "user", payload.message)
        guardar_mensaje(payload.user_id, "bot", resultado["respuesta"])
        
        return {"reply": resultado["respuesta"]}
        
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}")
        # Lanzar error 500 para que el cliente sepa que el servidor falló
        raise HTTPException(status_code=500, detail="Error interno al procesar el chat")
