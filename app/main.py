"""BiteFixes SaaS Backend entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database.supabase import supabase_manager
from app.routers import business_context, chat, customers, tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print(f"{settings.PROJECT_NAME} {settings.VERSION}")
    print(f"Engine : {settings.ENGINE}")
    print("Status : ONLINE")
    print("=" * 60)

    connected = supabase_manager.check_connection()
    print("Supabase : CONNECTED" if connected else "Supabase : CONNECTION FAILED")

    yield
    print("BiteFixes Backend shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="BiteFixes SaaS Backend powered by Bitey AI Engine",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        print("[GLOBAL ERROR]", exc)
    else:
        print("[GLOBAL ERROR]", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"},
    )


app.include_router(chat.router)
app.include_router(customers.router)
app.include_router(tickets.router)
app.include_router(business_context.router)


@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "engine": settings.ENGINE,
        "status": "online",
        "architecture": "FastAPI + Bitey AI + Supabase",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "bitefixes-backend"}


@app.get("/info")
def info():
    return {
        "company": "BiteFixes",
        "ai_engine": "Bitey",
        "database": "Supabase",
        "channels": ["website", "whatsapp", "mobile_app"],
        "status": "running",
    }


@app.get("/test-supabase")
def test_supabase():
    connected = supabase_manager.check_connection()
    return {
        "status": "ok" if connected else "error",
        "database": "Supabase connected" if connected else "Connection failed",
    }
