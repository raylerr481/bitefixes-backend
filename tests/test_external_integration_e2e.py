from app.services.integration_orchestrator import prepare_openapi_tools
from app.services.openapi_registry import normalize_candidates


def test_external_integration_prepare_pipeline_is_fail_closed():
    document = {
        "openapi": "3.0.3",
        "info": {"title": "Fixture API", "version": "1.0.0"},
        "paths": {
            "/customers": {
                "get": {
                    "operationId": "customers_list",
                    "summary": "List customers",
                },
            },
            "/customers/{id}": {
                "get": {"operationId": "customer_get"},
            },
            "/customers": {
                "post": {"operationId": "customer_create"},
            },
        },
    }
    prepared = prepare_openapi_tools(document)
    assert prepared["status"] == "prepared"
    assert prepared["permissions_granted"] is False
    assert prepared["executed"] is False
    assert all(t["action"] == "read" for t in prepared["tools"])


def test_write_candidate_cannot_cross_registry_boundary():
    try:
        normalize_candidates([
            {"code": "customer_create", "method": "POST", "path": "/customers"}
        ])
    except ValueError:
        return
    raise AssertionError("write candidate crossed the read-only registry boundary")
