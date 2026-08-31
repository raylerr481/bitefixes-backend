"""CME Bitey: Cognitive Multi-tenant Engine.

CME Bitey is the tenant-aware identity/context layer around the generic Bitey
cognitive engine.  It deliberately contains no industry-specific rules.

The engine can power different branded assistants while keeping tenant data,
identity and research context isolated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CompanyContext:
    """Business configuration supplied to the shared Bitey cognitive core."""

    company_id: str
    company_name: str
    assistant_name: str
    industry: str = "general"
    language: str = "es"
    currency: str = "BRL"
    services: tuple[str, ...] = ()
    business_rules: dict[str, Any] = field(default_factory=dict)
    knowledge_namespace: str | None = None


@dataclass(frozen=True)
class CMERequestContext:
    """Immutable request context passed to cognitive capabilities."""

    company: CompanyContext
    customer_id: str | None = None
    conversation_id: str | None = None

    @property
    def tenant_key(self) -> str:
        return self.company.company_id

    @property
    def assistant_identity(self) -> str:
        return self.company.assistant_name

    def research_context(self, *, problem: str | None = None,
                         category: str | None = None,
                         object_name: str | None = None,
                         model: str | None = None) -> dict[str, Any]:
        """Build tenant-scoped research context without embedding company rules."""
        return {
            "company_id": self.company.company_id,
            "company_name": self.company.company_name,
            "assistant_name": self.company.assistant_name,
            "industry": self.company.industry,
            "language": self.company.language,
            "problem": problem,
            "category": category,
            "object": object_name,
            "model": model,
        }


def make_cme_context(config: dict[str, Any]) -> CMERequestContext:
    """Create a validated tenant context from configuration/database data."""
    required = ("company_id", "company_name", "assistant_name")
    missing = [key for key in required if not str(config.get(key, "")).strip()]
    if missing:
        raise ValueError(f"Missing company context fields: {', '.join(missing)}")

    services = config.get("services") or ()
    return CMERequestContext(
        company=CompanyContext(
            company_id=str(config["company_id"]),
            company_name=str(config["company_name"]),
            assistant_name=str(config["assistant_name"]),
            industry=str(config.get("industry") or "general"),
            language=str(config.get("language") or "es"),
            currency=str(config.get("currency") or "BRL"),
            services=tuple(str(item) for item in services),
            business_rules=dict(config.get("business_rules") or {}),
            knowledge_namespace=(str(config["knowledge_namespace"])
                                if config.get("knowledge_namespace") else None),
        )
    )
