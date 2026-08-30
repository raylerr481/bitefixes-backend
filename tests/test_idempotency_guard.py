from app.cognitive.idempotency_guard import IdempotencyGuard, message_fingerprint


def test_same_message_has_same_fingerprint():
    assert message_fingerprint("hola", conversation_id="c1", sender="u1") == message_fingerprint("hola", conversation_id="c1", sender="u1")


def test_different_conversations_do_not_collide():
    assert message_fingerprint("hola", conversation_id="c1", sender="u1") != message_fingerprint("hola", conversation_id="c2", sender="u1")


def test_duplicate_is_processed_once():
    guard = IdempotencyGuard()
    calls = []

    def handler():
        calls.append(1)
        return {"answer": "ok"}

    first = guard.process("k", handler)
    second = guard.process("k", handler)
    assert first == second
    assert len(calls) == 1
