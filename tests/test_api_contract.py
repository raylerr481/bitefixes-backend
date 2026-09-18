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
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "bitefixes-backend"
    assert body["gateway"] == "bitey-cloud"
    assert body["bitey_trainer"] == "ready"
    assert body["crm"] == "ready"


def test_gateway_contract():
    response = client.get("/gateway/status")
    assert response.status_code == 200
    body = response.json()
    assert body["gateway"] == "bitey-cloud"
    assert body["brain"] == "bitey-core"
    assert body["single_entrypoint"] == "/chat"
    assert body["webhook_entrypoint"] == "/webhooks/{channel}"
    assert body["trainer_entrypoint"] == "/bitey-trainer"
    assert body["crm_entrypoint"] == "/portal/crm"
    assert "customer_channels" in body


def test_chat_rejects_missing_message_without_hitting_gateway():
    response = client.post("/chat", json={"company_id": 1, "message": "", "channel": "website"})
    assert response.status_code == 422
