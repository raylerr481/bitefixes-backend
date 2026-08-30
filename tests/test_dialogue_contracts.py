"""Conversational acceptance contracts for Bitey.

These tests intentionally validate response semantics without calling Render,
Supabase, WhatsApp, or an external LLM. They protect the user-visible rules
that the deterministic context layer must satisfy before a response is built.
"""

from app.services.problem_identity_service import ProblemIdentityService


def analyze(message, active=None):
    svc = ProblemIdentityService()
    return svc.analyze_problem(
        message,
        customer_id=1,
        active_problem=active,
        active_device=active.get("device") if active else None,
        active_platform=active.get("platform") if active else None,
    )


def test_windows_10_update_must_not_reset_diagnosis():
    first = analyze("tengo mi pc lenta con windows")
    second = analyze("windows 10", first)

    assert second["is_continuation"] is True
    assert second["is_new"] is False
    assert second.get("device") in {"computer", "pc"}
    assert "windows" in str(second.get("platform", "")).lower()
    assert any(x in str(second.get("category", "")).lower() for x in ("slow", "performance"))


def test_heating_followup_must_preserve_pc_context():
    first = analyze("mi pc con windows esta lenta")
    second = analyze("tambien se calienta", first)

    assert second["is_continuation"] is True
    assert second["is_new"] is False
    assert second.get("device") == first.get("device")


def test_explicit_device_switch_is_new_problem():
    first = analyze("mi pc esta lenta con windows")
    second = analyze("ahora mi celular no enciende", first)

    assert second["is_new"] is True
    assert second["is_continuation"] is False


def test_phone_os_update_preserves_phone_problem():
    first = analyze("mi celular no enciende")
    second = analyze("es android", first)

    assert second["is_continuation"] is True
    assert second["is_new"] is False
    assert second.get("device") in {"mobile", "phone", "cellphone", "smartphone"}
