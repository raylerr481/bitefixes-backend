import os
import google.generativeai as genai

# Configuração da chave de API
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Instruções do sistema reforçadas
system_instruction = (
    "Você é o Bitey, o assistente técnico oficial da BiteFixes. "
    "Sua função é auxiliar clientes com suporte técnico em computadores, redes, "
    "servidores, celulares e câmeras de segurança. "
    "REGRA OBRIGATÓRIA: Responda EXCLUSIVAMENTE em português brasileiro, "
    "independentemente do idioma em que o usuário enviar a mensagem. "
    "Seja prestativo, profissional e técnico."
)

generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

# Usamos a versão 001, que é a versão estável mais compatível atualmente
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-001", 
    generation_config=generation_config,
    system_instruction=system_instruction
)

def procesar_con_bitey(texto: str, user_id: str, historial: list):
    """
    Recibe el texto, el ID del usuario y el historial previo.
    """
    try:
        # Convertimos el historial de Supabase al formato que espera Gemini
        formatted_history = [
            {"role": "user" if h["sender"] == "user" else "model", "parts": [h["text"]]}
            for h in historial
        ]
        
        # Iniciamos una sesión con el historial cargado
        chat = model.start_chat(history=formatted_history)
        response = chat.send_message(texto)
        
        return {"respuesta": response.text}
        
    except Exception as e:
        # Lógica de diagnóstico: se houver erro, listamos os modelos disponíveis
        try:
            modelos_disponiveis = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
            return {"respuesta": f"Erro ao processar com Bitey: {str(e)}. Modelos disponíveis na conta: {modelos_disponiveis}"}
        except:
            return {"respuesta": f"Erro ao processar com Bitey: {str(e)}"}
