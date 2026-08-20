from app.services.incident_service import fingerprint


def test_fingerprint_is_stable():
    assert fingerprint("AI", "429", "Quota", "/chat", "Gemini", "generate", "quota exceeded") == fingerprint("ai", "429", "quota", "/chat", "gemini", "generate", "quota exceeded")


def test_fingerprint_changes_with_component():
    assert fingerprint("ai", "429") != fingerprint("rag", "429")
