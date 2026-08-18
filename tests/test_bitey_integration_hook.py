from app.core import bitey


def test_external_integration_hook_is_inert_without_explicit_request():
    assert bitey._prepare_external_integration({}) is None


def test_external_integration_hook_prepares_only_and_never_executes():
    result = bitey._prepare_external_integration({
        "external_integration": {
            "openapi_document": {
                "openapi": "3.0.3",
                "paths": {
                    "/customers": {"get": {"operationId": "customers_list"}},
                    "/orders": {"post": {"operationId": "orders_create"}},
                },
            }
        }
    })
    assert result["status"] == "prepared"
    assert result["executed"] is False
    assert result["permissions_granted"] is False
    assert [tool["code"] for tool in result["tools"]] == ["openapi.customers_list"]
