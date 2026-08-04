import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client


# =====================================================
# CARGAR VARIABLES DE ENTORNO
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_PATH = BASE_DIR / ".env"

load_dotenv(
    dotenv_path=ENV_PATH
)


# =====================================================
# LEER CONFIGURACIÓN SUPABASE
# =====================================================

SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY"
)


# =====================================================
# VALIDACIÓN
# =====================================================

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception(
        "Faltan variables SUPABASE_URL o SUPABASE_KEY"
    )


# =====================================================
# CLIENTE SUPABASE
# =====================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


print(
    "✅ Supabase conectado correctamente"
)