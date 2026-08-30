"""Deterministic dialogue regression tests for Bitey problem continuity.

These tests exercise the real Problem Identity API used by Bitey Core without
requiring Render, Supabase, or an external AI provider.
"""

from app.services.problem_identity_service import analyze_problem


def test_pc_slow_then_windows_10_is_context_update():
    first = analyze_problem(
        "tengo mi pc lenta con windows",
        current_intent="slow_performance",
    )

    second = analyze_problem(
        "windows 10",
        current_intent="slow_performance",
        active_intent=first.get("intent"),
        active_problem=first,
        active_device=first.get("device"),
        context={
            "language": "es",
            "last_platform": first.get("platform"),
            "last_os_version": first.get("os_version"),
        },
    )

    assert second["is_continuation"] is True
    assert second["is_new"] is False
    assert second.get("device") == first.get("device")
    assert "windows" in str(second.get("platform", "")).lower()
    assert second.get("os_version") == "Windows 10"
    assert second.get("category") == first.get("category")


def test_followup_keeps_pc_problem_identity():
    first = analyze_problem(
        "mi pc con windows esta lenta",
        current_intent="slow_performance",
    )

    second = analyze_problem(
        "tambien se calienta",
        current_intent=first.get("intent"),
        active_intent=first.get("intent"),
        active_problem=first,
        active_device=first.get("device"),
        context={"language": "es", "last_platform": first.get("platform")},
    )

    assert second["is_continuation"] is True
    assert second["is_new"] is False
    assert second.get("device") == first.get("device")
    assert second.get("category") == first.get("category")


def test_switching_to_phone_is_new_problem():
    first = analyze_problem(
        "mi pc esta lenta con windows",
        current_intent="slow_performance",
    )

    second = analyze_problem(
        "ahora mi celular no enciende",
        current_intent="power",
        active_intent=first.get("intent"),
        active_problem=first,
        active_device=first.get("device"),
        context={"language": "es", "last_platform": first.get("platform")},
    )

    assert second["is_new"] is True
    assert second["is_continuation"] is False
    assert second.get("device_kind") == "mobile"
    assert second.get("category") == "power"


def test_phone_followup_does_not_lose_phone_context():
    first = analyze_problem(
        "mi celular no enciende",
        current_intent="power",
    )

    second = analyze_problem(
        "es android",
        current_intent=first.get("intent"),
        active_intent=first.get("intent"),
        active_problem=first,
        active_device=first.get("device"),
        context={"language": "es", "last_platform": first.get("platform")},
    )

    assert second["is_continuation"] is True
    assert second["is_new"] is False
    assert second.get("device_kind") == "mobile"
    assert second.get("platform") == "android"
    assert second.get("category") == first.get("category")
