"""General continuity harness for Bitey problem identity.

These tests intentionally exercise the same analyze_problem() mechanism for
all scenarios. No scenario-specific production rules are introduced here.
"""
from app.services.problem_identity_service import analyze_problem


def run_turn(message, *, active_problem=None, active_intent=None, active_device=None, context=None):
    return analyze_problem(
        message=message,
        current_intent=None,
        active_intent=active_intent,
        active_problem=active_problem,
        active_device=active_device,
        context=context or {"language": "es"},
    )


def test_cctv_continuity():
    first = run_turn("Necesito instalar una cámara CCTV en mi negocio")
    second = run_turn(
        "¿Cuánto cuesta?",
        active_problem=first["category"],
        active_intent=first["intent"],
        active_device=first["device"],
    )
    assert first["state"] == "NEW_PROBLEM"
    assert second["state"] == "CONTINUATION"
    assert second["coherence"]["active_problem_preserved"] is True


def test_windows_server_vm_continuity():
    first = run_turn("Tengo un problema con Windows Server en mi servidor")
    second = run_turn(
        "La máquina virtual no inicia",
        active_problem=first["category"],
        active_intent=first["intent"],
        active_device=first["device"],
    )
    assert first["state"] == "NEW_PROBLEM"
    assert second["state"] in {"CONTINUATION", "RELATED_PROBLEM"}


def test_notebook_slow_continuity():
    first = run_turn("Mi notebook está muy lento")
    second = run_turn(
        "¿Qué puedo hacer para solucionarlo?",
        active_problem=first["category"],
        active_intent=first["intent"],
        active_device=first["device"],
    )
    assert first["state"] == "NEW_PROBLEM"
    assert second["state"] == "CONTINUATION"
    assert second["category"] == first["category"]


def test_mobile_change_of_problem():
    first = run_turn("Mi celular está muy lento")
    second = run_turn(
        "Ahora la pantalla está rota",
        active_problem=first["category"],
        active_intent=first["intent"],
        active_device=first["device"],
    )
    assert first["state"] == "NEW_PROBLEM"
    assert second["state"] == "NEW_PROBLEM"
    assert second["category"] == "screen"


def test_no_invented_context():
    result = run_turn("s")
    assert result["state"] in {"NEW_PROBLEM", "NEEDS_CLARIFICATION"}
    assert result["problem_summary"] in {None, "unknown"} or result["category"] is None


def test_same_mechanism_is_used_for_all_cases():
    """Meta-test: all scenarios above call only run_turn -> analyze_problem."""
    assert run_turn.__code__.co_names.count("analyze_problem") == 1
