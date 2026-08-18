import pytest

from app.services.openapi_registry import OpenAPIRegistryError, normalize_candidates


def test_normalizes_read_candidates_and_requires_permission():
    candidates = normalize_candidates([
        {"code": "openapi.customers", "name": "Customers", "method": "get", "path": "/customers"},
        {"code": "openapi.customers", "name": "Duplicate", "method": "GET", "path": "/customers"},
    ])
    assert len(candidates) == 1
    assert candidates[0]["action"] == "read"
    assert candidates[0]["default_deny"] is True
    assert candidates[0]["requires_permission"] is True


def test_rejects_write_candidate():
    with pytest.raises(OpenAPIRegistryError):
        normalize_candidates([
            {"code": "openapi.order_create", "method": "POST", "path": "/orders"}
        ])


def test_rejects_missing_path():
    with pytest.raises(OpenAPIRegistryError):
        normalize_candidates([{"code": "openapi.test", "method": "GET"}])
