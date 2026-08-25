"""BiteFixes SaaS Backend entrypoint."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database.supabase import supabase_manager
from app.routers import business_context, chat, customers, tickets, ai, webhooks, company_profile, bitey_trainer
from app.ai.runtime import build_ai_orchestrator
from app.ai.free_policy import FREE_ONLY, max_estimated_cost

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print(f"{settings.PROJECT_NAME} {settings.VERSION}")
    print(f"Engine : {settings.ENGINE}")
    print("Status : ONLINE")
    connected = supabase_manager.check_connection()
    print("Supabase : CONNECTED" if connected else "Supabase : CONNECTION FAILED")
    orchestrator = build_ai_orchestrator()
    available = [spec.name for spec in orchestrator.registry.available("general_reasoning")]
    print("AI Providers : " + (", ".join(available) if available else "NONE"))
    print(f"AI Free-Only : {'ENABLED' if FREE_ONLY else 'DISABLED'}")
    print("Web Intelligence : ENABLED")
    print("Bitey Gateway : ENABLED")
    print("Bitey Trainer : ENABLED")
    yield
    print("BiteFixes Backend shutting down...")

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, description="BiteFixes SaaS Backend powered by Bitey AI Engine and unified cloud gateway", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], allow_headers=["Authorization", "Content-Type", "Accept", "Origin"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("[GLOBAL ERROR]", exc if settings.DEBUG else type(exc).__name__)
    return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

app.include_router(chat.router)
app.include_router(customers.router)
app.include_router(tickets.router)
app.include_router(business_context.router)
app.include_router(ai.router)
app.include_router(webhooks.router)
app.include_router(company_profile.router)
app.include_router(bitey_trainer.router)

@app.get("/")
def root():
    return {"project": settings.PROJECT_NAME, "version": settings.VERSION, "engine": settings.ENGINE, "status": "online", "architecture": "Bitey Cloud Gateway + Bitey Core + Supabase + governed free-only AI providers + Bitey Trainer"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "bitefixes-backend", "gateway": "bitey-cloud", "bitey_trainer": "ready"}

@app.get("/info")
def info():
    return {"company": "BiteFixes", "ai_engine": "Bitey", "database": "Supabase", "architecture": "single-cloud-brain-multi-channel", "channels": ["website", "whatsapp", "messenger", "telegram", "email", "sms", "phone", "app", "private", "api"], "chat_gateway": "/chat", "webhook_gateway": "/webhooks/{channel}", "company_profile_ingestion": "/company-profile/import", "trainer_gateway": "/bitey-trainer", "status": "running"}

@app.get("/gateway/status")
def gateway_status():
    return {"gateway": "bitey-cloud", "status": "ready", "brain": "bitey-core", "single_entrypoint": "/chat", "webhook_entrypoint": "/webhooks/{channel}", "trainer_entrypoint": "/bitey-trainer", "channels": ["website", "whatsapp", "messenger", "telegram", "email", "sms", "phone", "app", "private", "api"], "identity": "centralized-customer-conversation-memory"}

@app.get("/ai/status")
def ai_status():
    orchestrator = build_ai_orchestrator()
    providers = []
    for spec in orchestrator.registry._providers.values():
        providers.append({"name": spec.name, "enabled": bool(spec.enabled and spec.provider), "cost_class": spec.cost_class, "eligible": bool(spec.enabled and spec.provider and spec.cost_class == "free"), "capabilities": list(spec.capabilities)})
    return {"engine": "Bitey", "status": "ready", "gateway": "ready", "supabase": bool(supabase_manager.check_connection()), "web_intelligence": {"enabled": True, "service": "bitey-search-core"}, "external_ai": {"providers": providers, "available_general_reasoning": [p["name"] for p in providers if p["eligible"] and "general_reasoning" in p["capabilities"]]}, "policy": {"free_only": FREE_ONLY, "consult_min_confidence": float(os.getenv("AI_CONSULT_MIN_CONFIDENCE", "0.78")), "max_estimated_cost": max_estimated_cost(), "max_providers": int(os.getenv("AI_COUNCIL_MAX_PROVIDERS", "2"))}}

@app.get("/test-supabase")
def test_supabase():
    connected = supabase_manager.check_connection()
    return {"status": "ok" if connected else "error", "database": "Supabase connected" if connected else "Connection failed"}
