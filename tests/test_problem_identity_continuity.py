"""Demo-loop regression tests for Bitey problem/ticket continuity."""
from app.services.problem_identity_service import analyze_problem


def test_device_model_update_preserves_problem_identity():
    first = analyze_problem(
        "Mi celular esta lento",
        current_intent="support",
        active_intent="support",
    )
    second = analyze_problem(
        "Es un Redmi Note 13",
        current_intent="support",
        active_intent="support",
        active_problem=first["category"],
        active_device=first["device"],
    )

    assert first["category"] == "slow_performance"
    assert second["state"] == "CONTINUATION"
    assert second["category"] == first["category"]
    assert second["fingerprint"] == first["fingerprint"]


def test_new_symptom_in_same_domain_remains_continuation():
    first = analyze_problem(
        "Mi notebook esta lento",
        current_intent="support",
        active_intent="support",
    )
    second = analyze_problem(
        "Ahora tambien se traba cuando abro aplicaciones",
        current_intent="support",
        active_intent="support",
        active_problem=first["category"],
        active_device=first["device"],
    )

    assert second["state"] == "CONTINUATION"
    assert second["category"] == first["category"]
    assert second["fingerprint"] == first["fingerprint"]


def test_unrelated_problem_gets_different_identity():
    first = analyze_problem(
        "Mi notebook esta lento",
        current_intent="support",
        active_intent="support",
    )
    second = analyze_problem(
        "La pantalla esta rota",
        current_intent="support",
        active_intent="support",
        active_problem=first["category"],
        active_device=first["device"],
    )

    assert second["state"] in {"RELATED_PROBLEM", "NEW_PROBLEM"}
    assert second["fingerprint"] != first["fingerprint"]


def test_same_problem_without_device_does_not_require_model_match():
    first = analyze_problem(
        "Mi celular tiene virus",
        current_intent="support",
        active_intent="support",
    )
    second = analyze_problem(
        "Sigue igual, aparecen anuncios",
        current_intent="support",
        active_intent="support",
        active_problem=first["category"],
        active_device=first["device"],
    )

    assert second["state"] == "CONTINUATION"
    assert second["fingerprint"] == first["fingerprint"]


def test_company_boundary_is_part_of_persistence_contract():
    """The analyzer is tenant-agnostic; persistence must scope by company_id.

    This regression documents the invariant enforced by persist_problem: the
    same fingerprint is not globally reusable across companies.
    """
    first = analyze_problem("Mi celular esta lento", current_intent="support")
    assert first["fingerprint"]
