"""Typed business context contract used by Bitey orchestration."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BusinessContextSummary(BaseModel):
    company_id: int
    company: Optional[Dict[str, Any]] = None
    business_profile: Optional[Dict[str, Any]] = None
    industries: List[Dict[str, Any]] = Field(default_factory=list)
    business_models: List[Dict[str, Any]] = Field(default_factory=list)
    business_functions: List[Dict[str, Any]] = Field(default_factory=list)
    subscription: Optional[Dict[str, Any]] = None
    ai_scope: Optional[Dict[str, Any]] = None
    domains: List[Dict[str, Any]] = Field(default_factory=list)
    capabilities: List[Dict[str, Any]] = Field(default_factory=list)
    services: List[Dict[str, Any]] = Field(default_factory=list)
    knowledge: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = {"extra": "allow"}
