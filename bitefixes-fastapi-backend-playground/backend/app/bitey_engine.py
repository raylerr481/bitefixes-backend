import os
import google.generativeai as genai

# Configuração da chave de API (certifique-se de que a variável de ambiente esteja definida)
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Definição das instruções do sistema para garantir o idioma português
# e definir a personalidade do Bitey.
system_instruction = (
    "Você é o Bitey, o assistente técnico oficial da BiteFixes. "
    "Sua função é auxiliar clientes com suporte técnico em computadores, redes, "
    "servidores, celulares e câmeras de segurança. "
    "Responda EXCLUSIVAMENTE em português brasileiro. "
    "Seja prestativo, profissional e técnico."
)

# Configuração do modelo
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction=system_instruction
)

def procesar_con_bitey(prompt_usuario):
    """
    Recebe a pergunta do usuário e retorna a resposta do Bitey.
    """
    try:
        chat = model.start_chat(history=[])
        response = chat.send_message(prompt_usuario)
        return response.text
    except Exception as e:
        return f"Erro ao processar com Bitey: {str(e)}"
