"""Bitey AI orchestration package."""

from .registry import AIProviderRegistry, ProviderSpec
from .orchestrator import AIOrchestrator
from .apprentice import build_learning_context, evaluate_bitey, provider_role

__all__ = [
    "AIProviderRegistry",
    "ProviderSpec",
    "AIOrchestrator",
    "build_learning_context",
    "evaluate_bitey",
    "provider_role",
]
