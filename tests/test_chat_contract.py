"""Contract tests for the public Bitey chat boundary."""
from app.schemas.chat_schema import ChatRequest


def test_chat_request_normalizes_expected_defaults():
    request = ChatRequest(message="Tengo la pantalla rota")
    assert request.company_id == 1
    assert request.channel == "website"
    assert request.language_preference == "auto"
    assert request.conversation_id is None


def test_chat_request_preserves_session_context():
    request = ChatRequest(
        message="Necesito reparar mi celular",
        phone="+5511999999999",
        customer_name="Rayler",
        conversation_id="conv-123",
        language_preference="es",
    )
    assert request.phone.startswith("+")
    assert request.customer_name == "Rayler"
    assert request.conversation_id == "conv-123"
    assert request.language_preference == "es"
