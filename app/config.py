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
    VERSION = "2.4.0"
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

    # Bitey Web Intelligence
    BITEY_SEARCH_PRIMARY_URL = os.getenv("BITEY_SEARCH_PRIMARY_URL")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    BITEY_WEB_SEARCH_TIMEOUT = float(os.getenv("BITEY_WEB_SEARCH_TIMEOUT", "8"))
    BITEY_WEB_CACHE_TTL = int(os.getenv("BITEY_WEB_CACHE_TTL", "900"))
    BITEY_WEB_MAX_QUERIES = int(os.getenv("BITEY_WEB_MAX_QUERIES", "3"))
    BITEY_WEB_MAX_RESULTS = int(os.getenv("BITEY_WEB_MAX_RESULTS", "8"))
    BITEY_WEB_VERIFY_SCORE = float(os.getenv("BITEY_WEB_VERIFY_SCORE", "0.72"))
    BITEY_WEB_MEMORY_TTL = int(os.getenv("BITEY_WEB_MEMORY_TTL", "2592000"))
    BITEY_WEB_MEMORY_MAX_RESULTS = int(os.getenv("BITEY_WEB_MEMORY_MAX_RESULTS", "5"))

    # AI provider routing. Providers are optional and fail closed to Bitey Core.
    AI_DEFAULT_PROVIDER = os.getenv("AI_DEFAULT_PROVIDER", "ollama")
    AI_FALLBACK_PROVIDERS = os.getenv(
        "AI_FALLBACK_PROVIDERS", "gemini,groq,huggingface"
    )
    AI_REQUEST_TIMEOUT = float(os.getenv("AI_REQUEST_TIMEOUT", "30"))
    AI_MAX_OUTPUT_TOKENS = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "800"))

    # Google Gemini API: optional; use only when a valid key is configured.
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Groq Cloud: optional OpenAI-compatible API.
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # Hugging Face: optional Serverless Inference API.
    HF_API_TOKEN = os.getenv("HF_API_TOKEN")
    HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Llama-3.2-3B-Instruct")

    # Ollama: local/open-source provider; no cloud key required.
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    # Optional vector backends. They are additive; Supabase remains the system of record.
    VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "none")
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "bitey_knowledge")


settings = Settings()
