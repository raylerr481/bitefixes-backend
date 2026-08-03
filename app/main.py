"""
BiteFixes SaaS Backend

Main FastAPI Application.

Architecture:

Channels
    |
    v
FastAPI Routers
    |
    v
Bitey AI Core Engine
    |
    v
Services Layer
    |
    v
Supabase Database
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database.supabase import supabase_manager

from app.routers import (
    chat,
    customers,
    tickets,
)


# =====================================================
# APPLICATION LIFECYCLE
# =====================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("=" * 60)
    print(f"{settings.PROJECT_NAME} {settings.VERSION}")
    print(f"Engine : {settings.ENGINE}")
    print("Status : ONLINE")
    print("=" * 60)

    connected = supabase_manager.check_connection()

    if connected:
        print("Supabase : CONNECTED")
    else:
        print("Supabase : CONNECTION FAILED")

    yield

    print("BiteFixes Backend shutting down...")


# =====================================================
# APPLICATION INSTANCE
# =====================================================

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "BiteFixes SaaS Backend powered by "
        "Bitey AI Engine"
    ),
    lifespan=lifespan,
)


# =====================================================
# CORS CONFIGURATION
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=[
        "*"
    ],
    allow_headers=[
        "*"
    ],
)


# =====================================================
# GLOBAL ERROR HANDLER
# =====================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):

    print(
        "[GLOBAL ERROR]",
        exc
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
        },
    )


# =====================================================
# ROUTERS
# =====================================================

app.include_router(
    chat.router
)

app.include_router(
    customers.router
)

app.include_router(
    tickets.router
)


# =====================================================
# ROOT STATUS
# =====================================================

@app.get("/")
def root():

    return {

        "project": settings.PROJECT_NAME,

        "version": settings.VERSION,

        "engine": settings.ENGINE,

        "status": "online",

        "architecture": (
            "FastAPI + Bitey AI + Supabase"
        ),

    }


# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/health")
def health():

    return {

        "status": "ok",

        "service": (
            "bitefixes-backend"
        ),

    }


# =====================================================
# SYSTEM INFORMATION
# =====================================================

@app.get("/info")
def info():

    return {

        "company": "BiteFixes",

        "ai_engine": "Bitey",

        "database": "Supabase",

        "channels": [

            "website",

            "whatsapp",

            "mobile_app",

        ],

        "status": "running",

    }


# =====================================================
# SUPABASE TEST
# =====================================================

@app.get("/test-supabase")
def test_supabase():

    connected = (
        supabase_manager
        .check_connection()
    )


    if connected:

        return {

            "status": "ok",

            "database": (
                "Supabase connected"
            ),

        }


    return {

        "status": "error",

        "database": (
            "Connection failed"
        ),

    }