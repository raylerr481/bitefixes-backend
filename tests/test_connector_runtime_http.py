"""Controlled runtime execution tests.

The HTTP client is replaced with a deterministic fixture, so no external
network is contacted by this suite.
"""

from app.services import connector_runtime


def test_authorized_get_executes_against_controlled_fixture(monkeypatch):
    class Allowed:
        allowed = True
        requires_approval = False
        reason = "permission_granted"

    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"customers": [{"id": 1, "name": "Fixture Customer"}]}

    class Client:
        def __init__(self, *args, **kwargs):
            self.calls = []

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, headers=None):
            self.calls.append((url, headers))
            return Response()

    monkeypatch.setattr(connector_runtime, "evaluate_permission", lambda **kwargs: Allowed())
    monkeypatch.setattr(connector_runtime.httpx, "Client", Client)

    result = connector_runtime.execute_rest_read(
        company_id=1,
        tool_code="rest_api_resource",
        connection={"id": 1, "endpoint_url": "https://fixture.example.com/api"},
        path="customers",
        dry_run=False,
    )

    assert result["executed"] is True
    assert result["status_code"] == 200
    assert result["data"] == {"customers": [{"id": 1, "name": "Fixture Customer"}]}


def test_authorized_get_dry_run_never_constructs_http_client(monkeypatch):
    class Allowed:
        allowed = True
        requires_approval = False
        reason = "permission_granted"

    def fail_if_called(*args, **kwargs):
        raise AssertionError("HTTP client must not be constructed in dry-run")

    monkeypatch.setattr(connector_runtime, "evaluate_permission", lambda **kwargs: Allowed())
    monkeypatch.setattr(connector_runtime.httpx, "Client", fail_if_called)

    result = connector_runtime.execute_rest_read(
        company_id=1,
        tool_code="rest_api_resource",
        connection={"id": 1, "endpoint_url": "https://fixture.example.com/api"},
        path="customers",
        dry_run=True,
    )

    assert result["executed"] is False
    assert result["dry_run"] is True
