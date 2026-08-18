from app.services.openapi_discovery import OpenAPIDiscoveryError, discover_tools


def test_discovers_only_read_operations():
    doc = {
        "openapi": "3.0.3",
        "paths": {
            "/customers": {"get": {"operationId": "customers_list", "summary": "List customers"}},
            "/orders": {"post": {"operationId": "orders_create"}},
            "/orders/{id}": {"get": {"operationId": "order_get"}},
            "/health": {"head": {"operationId": "health_check"}},
        },
    }
    tools = discover_tools(doc)
    assert [tool["code"] for tool in tools] == [
        "openapi.customers_list",
        "openapi.order_get",
        "openapi.health_check",
    ]
    assert all(tool["action"] == "read" for tool in tools)
    assert all(tool["default_deny"] for tool in tools)


def test_rejects_non_openapi3():
    try:
        discover_tools({"openapi": "2.0", "paths": {}})
    except OpenAPIDiscoveryError as exc:
        assert str(exc) == "only_openapi_3_supported"
    else:
        raise AssertionError("expected OpenAPIDiscoveryError")


def test_ignores_invalid_path_items():
    doc = {"openapi": "3.0.0", "paths": {"/bad": None, "/ok": {"get": {}}}}
    tools = discover_tools(doc)
    assert len(tools) == 1
    assert tools[0]["method"] == "GET"
