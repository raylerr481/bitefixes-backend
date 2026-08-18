from dotenv import load_dotenv
import os

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    PROJECT_NAME = "BiteFixes Backend"
    VERSION = "2.1.0"
    ENGINE = "Bitey"

    # Supabase server-side connection. Never commit these values.
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = _env_bool("DEBUG", False)

    # Comma-separated browser origins. Keep empty for non-browser/API-only use.
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "https://www.bitefixes.com").split(",")
        if origin.strip()
    ]

    DEFAULT_LANGUAGE = "pt-BR"
    CONFIDENCE_MIN = 0.70


settings = Settings()
