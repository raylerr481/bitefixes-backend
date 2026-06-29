import os
import google.generativeai as genai
from supabase import create_client

# Configuración de servicios
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

def procesar_con_bitey(categoria, descripcion):
    # Instrucciones de sistema (lo que definimos antes)
    system_instruction = "Eres Bitey, el asistente técnico de BiteFixes..." 
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )
    
    # Pedimos a Bitey el diagnóstico técnico
    prompt = f"El cliente reporta un problema en {categoria}: {descripcion}"
    response = model.generate_content(prompt)
    diagnostico = response.text
    
    # Guardar en Supabase
    ticket_data = {
        "categoria": categoria,
        "descricao": descripcion,
        "log_tecnico": diagnostico,
        "status": "aberto"
    }
    
    supabase.table("tickets").insert(ticket_data).execute()
    
    return diagnostico