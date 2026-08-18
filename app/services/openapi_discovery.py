"""Safe OpenAPI discovery for Bitey integrations.

Discovery never executes an API operation. It converts an OpenAPI document
into normalized, read-only tool candidates for review/registration.
"""

from typing import Any, Dict, List


class OpenAPIDiscoveryError(ValueError):
    """Raised when an OpenAPI document is invalid or unsupported."""


def discover_tools(document: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return normalized tool candidates from an OpenAPI 3.x document."""
    if not isinstance(document, dict):
        raise OpenAPIDiscoveryError("openapi_document_must_be_object")

    version = str(document.get("openapi", ""))
    if not version.startswith("3."):
        raise OpenAPIDiscoveryError("only_openapi_3_supported")

    candidates: List[Dict[str, Any]] = []
    for path, path_item in (document.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            method = method.lower()
            if method not in {"get", "head"} or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId") or f"{method}_{str(path).strip('/').replace('/', '_') or 'root'}"
            candidates.append({
                "code": f"openapi.{operation_id}",
                "name": operation.get("summary") or operation_id,
                "action": "read",
                "method": method.upper(),
                "path": path,
                "description": operation.get("description") or operation.get("summary") or "",
                "default_deny": True,
            })

    return candidates
