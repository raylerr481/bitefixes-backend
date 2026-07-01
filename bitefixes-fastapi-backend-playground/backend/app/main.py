# Asegúrate de importar esto
from fastapi.responses import JSONResponse

# ... (resto de tus importaciones)

@app.post("/api/chat/direct")
async def chat_web(payload: ChatRequest):
    # Log de diagnóstico para ver qué llega realmente
    logger.info(f"Recibida petición de: {payload.user_id}")
    try:
        historial = obtener_historial(payload.user_id)
        resultado = procesar_con_bitey(payload.message, payload.user_id, historial)
        
        guardar_mensaje(payload.user_id, "user", payload.message)
        guardar_mensaje(payload.user_id, "bot", resultado["respuesta"])
        
        return {"reply": resultado["respuesta"]}
    except Exception as e:
        logger.error(f"Error crítico en backend: {e}")
        # Retornar un 500 para que el frontend no confunda el error
        return JSONResponse(status_code=500, content={"reply": "Error interno del servidor"})
