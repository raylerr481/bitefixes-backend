from app.cognitive.persistent_idempotency import request_fingerprint


def test_fingerprint_is_deterministic_and_scope_sensitive():
    a = request_fingerprint("identity:a", "hola")
    b = request_fingerprint("identity:a", "hola")
    c = request_fingerprint("identity:b", "hola")
    assert a == b
    assert a != c
