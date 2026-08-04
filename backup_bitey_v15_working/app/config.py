from dotenv import load_dotenv
import os

# Cargar variables del archivo .env
load_dotenv()

class Settings:
    # Información del proyecto
    PROJECT_NAME = "BiteFixes Backend"
    VERSION = "2.0.0"
    ENGINE = "Bitey"

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # API
    HOST = "127.0.0.1"
    PORT = 8000
    DEBUG = True

    # IA
    DEFAULT_LANGUAGE = "pt-BR"
    CONFIDENCE_MIN = 0.70


settings = Settings()