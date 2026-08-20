from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_contract():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["project"] == "BiteFixes Backend"
    assert body["engine"] == "Bitey"
    assert body["status"] == "online"


def test_health_contract():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "bitefixes-backend",
        "gateway": "bitey-cloud",
    }


def test_gateway_contract():
    response = client.get("/gateway/status")
    assert response.status_code == 200
    body = response.json()
    assert body["gateway"] == "bitey-cloud"
    assert body["brain"] == "bitey-core"
    assert body["single_entrypoint"] == "/chat"
    assert body["webhook_entrypoint"] == "/webhooks/{channel}"
    assert "website" in body["channels"]


def test_chat_route_is_registered():
    routes = {route.path for route in app.routes}
    assert "/chat" in routes


def test_chat_rejects_missing_message_without_hitting_gateway():
    response = client.post(
        "/chat",
        json={"company_id": 1, "message": "", "channel": "website"},
    )
    assert response.status_code == 422
