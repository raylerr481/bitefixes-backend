import os
import google.generativeai as genai

# Configuração da chave de API
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Instruções do sistema
system_instruction = (
    "Você é o Bitey, o assistente técnico oficial da BiteFixes. "
    "Sua função é auxiliar clientes com suporte técnico. "
    "Responda EXCLUSIVAMENTE em português brasileiro."
)

generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

# CAMBIO CRÍTICO: Usamos "gemini-3.5-flash" que confirmamos estar disponible en tu cuenta.
model = genai.GenerativeModel(
    model_name="gemini-3.5-flash", 
    generation_config=generation_config,
    system_instruction=system_instruction
)

def procesar_con_bitey(texto: str, user_id: str, historial: list):
    try:
        # Formateo del historial para la API de Gemini
        formatted_history = [
            {"role": "user" if h["sender"] == "user" else "model", "parts": [h["text"]]}
            for h in historial
        ]
        
        chat = model.start_chat(history=formatted_history)
        response = chat.send_message(texto)
        
        return {"respuesta": response.text}
        
    except Exception as e:
        # Bloque de diagnóstico: Si falla, nos devuelve la lista real de modelos disponibles
        try:
            lista = [m.name for m in genai.list_models()]
            return {"respuesta": f"Erro: {str(e)}. Modelos na sua API: {lista}"}
        except Exception as e2:
            return {"respuesta": f"Erro crítico: {str(e)} | Detalhe: {str(e2)}"}
