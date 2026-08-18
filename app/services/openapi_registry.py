"""Safe registration of discovered OpenAPI read tools.

Discovery produces candidates only. This module validates and normalizes
candidates before they can be considered for registration. It does not grant
permissions and never executes external API operations.
"""

from typing import Any, Dict, Iterable, List


class OpenAPIRegistryError(ValueError):
    """Raised when a discovered tool candidate cannot be registered."""


def normalize_candidates(candidates: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    seen = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise OpenAPIRegistryError("candidate_must_be_object")
        code = str(candidate.get("code", "")).strip()
        method = str(candidate.get("method", "")).upper()
        path = str(candidate.get("path", "")).strip()
        if not code or not path or method not in {"GET", "HEAD"}:
            raise OpenAPIRegistryError("only_read_candidates_are_registrable")
        if code in seen:
            continue
        seen.add(code)
        normalized.append({
            "code": code,
            "name": str(candidate.get("name") or code),
            "action": "read",
            "method": method,
            "path": path,
            "description": str(candidate.get("description") or ""),
            "default_deny": True,
            "requires_permission": True,
        })
    return normalized
