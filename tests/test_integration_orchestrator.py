from app.services.integration_orchestrator import prepare_openapi_tools


def test_prepare_openapi_tools_is_non_executing_and_non_authorizing():
    result = prepare_openapi_tools({
        "openapi": "3.0.3",
        "paths": {
            "/customers": {"get": {"operationId": "customers_list"}},
            "/orders": {"post": {"operationId": "orders_create"}},
        },
    })
    assert result["status"] == "prepared"
    assert result["count"] == 1
    assert result["permissions_granted"] is False
    assert result["executed"] is False
    assert result["tools"][0]["code"] == "openapi.customers_list"
