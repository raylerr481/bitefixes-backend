from app.services.connector_runtime import execute_rest_read


def test_rest_read_dry_run_does_not_execute():
    connection = {"id": 999999, "endpoint_url": "https://example.invalid/api"}
    result = execute_rest_read(
        company_id=999999,
        tool_code="rest_api_resource",
        connection=connection,
        path="customers",
        dry_run=True,
    )
    # No connection/permission exists, so policy must fail closed.
    assert result["executed"] is False


def test_missing_endpoint_fails_closed_after_authorization_boundary():
    connection = {"id": 999999, "endpoint_url": None}
    result = execute_rest_read(
        company_id=999999,
        tool_code="rest_api_resource",
        connection=connection,
        dry_run=True,
    )
    assert result["executed"] is False
