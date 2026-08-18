"""Orchestrates safe integration requests without executing unauthorized actions."""

from typing import Any, Dict

from app.services.openapi_discovery import discover_tools
from app.services.openapi_registry import normalize_candidates


def prepare_openapi_tools(document: Dict[str, Any]) -> Dict[str, Any]:
    """Discover and normalize read-only OpenAPI tools for review.

    This function has no database writes, grants no permissions, and performs
    no external API calls. Registration/activation remains a separate step.
    """
    candidates = discover_tools(document)
    tools = normalize_candidates(candidates)
    return {
        "status": "prepared",
        "count": len(tools),
        "tools": tools,
        "permissions_granted": False,
        "executed": False,
    }
