import pytest

from app.services.connector_runtime import ConnectorExecutionError, execute_rest_read


def _allow(monkeypatch):
    class Allowed:
        allowed = True
        requires_approval = False
        reason = "permission_granted"
    monkeypatch.setattr("app.services.connector_runtime.evaluate_permission", lambda **kwargs: Allowed())


def test_rest_read_dry_run_does_not_execute(monkeypatch):
    _allow(monkeypatch)
    connection = {"id": 999999, "endpoint_url": "https://example.invalid/api"}
    result = execute_rest_read(company_id=999999, tool_code="rest_api_resource", connection=connection, path="customers", dry_run=True)
    assert result["executed"] is False
    assert result["dry_run"] is True


def test_missing_endpoint_fails_closed_after_authorization_boundary(monkeypatch):
    _allow(monkeypatch)
    connection = {"id": 999999, "endpoint_url": None}
    with pytest.raises(ConnectorExecutionError, match="connection_endpoint_missing"):
        execute_rest_read(company_id=999999, tool_code="rest_api_resource", connection=connection, dry_run=True)


def test_authorized_private_target_is_still_blocked(monkeypatch):
    _allow(monkeypatch)
    with pytest.raises(ConnectorExecutionError, match="private_or_local_target_blocked"):
        execute_rest_read(1, "rest_api_resource", {"id": 1, "endpoint_url": "https://127.0.0.1/api"}, dry_run=True)


def test_authorized_http_target_is_blocked(monkeypatch):
    _allow(monkeypatch)
    with pytest.raises(ConnectorExecutionError, match="https_endpoint_required"):
        execute_rest_read(1, "rest_api_resource", {"id": 1, "endpoint_url": "http://api.example.com"}, dry_run=True)


def test_authorized_absolute_path_is_blocked(monkeypatch):
    _allow(monkeypatch)
    with pytest.raises(ConnectorExecutionError, match="connector_path_must_be_relative"):
        execute_rest_read(1, "rest_api_resource", {"id": 1, "endpoint_url": "https://api.example.com"}, path="https://evil.example.com/steal", dry_run=True)
