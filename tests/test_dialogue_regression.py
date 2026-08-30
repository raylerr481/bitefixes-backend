"""Dialogue regression cases for Bitey problem continuity and context accumulation.

These tests exercise the deterministic problem-identity layer without requiring
network access, external AI providers, Supabase, or Render.
"""

from app.services.problem_identity_service import ProblemIdentityService


def _service():
    return ProblemIdentityService()


def test_pc_slow_then_windows_10_is_context_update():
    svc = _service()

    first = svc.analyze_problem(
        "tengo mi pc lenta con windows",
        customer_id=1,
        active_problem=None,
        active_device=None,
        active_platform=None,
    )

    second = svc.analyze_problem(
        "windows 10",
        customer_id=1,
        active_problem=first,
        active_device=first.get("device"),
        active_platform=first.get("platform"),
    )

    assert second["is_continuation"] is True
    assert second["is_new"] is False
    assert second.get("device") in {"computer", "pc"}
    assert "windows" in str(second.get("platform", "")).lower()
    assert "slow" in str(second.get("category", "")).lower() or "performance" in str(second.get("category", "")).lower()


def test_followup_keeps_pc_problem_identity():
    svc = _service()

    first = svc.analyze_problem(
        "mi pc con windows esta lenta",
        customer_id=1,
        active_problem=None,
        active_device=None,
        active_platform=None,
    )

    second = svc.analyze_problem(
        "tambien se calienta",
        customer_id=1,
        active_problem=first,
        active_device=first.get("device"),
        active_platform=first.get("platform"),
    )

    assert second["is_continuation"] is True
    assert second["is_new"] is False
    assert second.get("device") == first.get("device")


def test_switching_to_phone_is_new_problem():
    svc = _service()

    first = svc.analyze_problem(
        "mi pc esta lenta con windows",
        customer_id=1,
        active_problem=None,
        active_device=None,
        active_platform=None,
    )

    second = svc.analyze_problem(
        "ahora mi celular no enciende",
        customer_id=1,
        active_problem=first,
        active_device=first.get("device"),
        active_platform=first.get("platform"),
    )

    assert second["is_new"] is True
    assert second["is_continuation"] is False


def test_phone_followup_does_not_lose_phone_context():
    svc = _service()

    first = svc.analyze_problem(
        "mi celular no enciende",
        customer_id=1,
        active_problem=None,
        active_device=None,
        active_platform=None,
    )

    second = svc.analyze_problem(
        "es android",
        customer_id=1,
        active_problem=first,
        active_device=first.get("device"),
        active_platform=first.get("platform"),
    )

    assert second["is_continuation"] is True
    assert second["is_new"] is False
    assert second.get("device") in {"mobile", "phone", "cellphone", "smartphone"}
