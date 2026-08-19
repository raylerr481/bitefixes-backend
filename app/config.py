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
    VERSION = "2.3.0"
    ENGINE = "Bitey"

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = _env_bool("DEBUG", False)

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "https://www.bitefixes.com").split(",")
        if origin.strip()
    ]

    DEFAULT_LANGUAGE = "pt-BR"
    CONFIDENCE_MIN = 0.70

    # Bitey Web Intelligence. Primary is Bitey-owned Search Core/SearXNG.
    # Tavily is an optional secondary fallback. Brave and similar providers are not supported.
    BITEY_SEARCH_PRIMARY_URL = os.getenv("BITEY_SEARCH_PRIMARY_URL")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    BITEY_WEB_SEARCH_TIMEOUT = float(os.getenv("BITEY_WEB_SEARCH_TIMEOUT", "8"))
    BITEY_WEB_CACHE_TTL = int(os.getenv("BITEY_WEB_CACHE_TTL", "900"))
    BITEY_WEB_MAX_QUERIES = int(os.getenv("BITEY_WEB_MAX_QUERIES", "3"))
    BITEY_WEB_MAX_RESULTS = int(os.getenv("BITEY_WEB_MAX_RESULTS", "8"))
    BITEY_WEB_VERIFY_SCORE = float(os.getenv("BITEY_WEB_VERIFY_SCORE", "0.72"))
    BITEY_WEB_MEMORY_TTL = int(os.getenv("BITEY_WEB_MEMORY_TTL", "2592000"))
    BITEY_WEB_MEMORY_MAX_RESULTS = int(os.getenv("BITEY_WEB_MEMORY_MAX_RESULTS", "5"))


settings = Settings()
