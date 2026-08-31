"""Objective continuity regression harness for Bitey's real problem-state mechanism."""
from app.services.problem_state_service import build_problem_state


def _turns(*messages):
    history = []
    states = []
    for message in messages:
        state = build_problem_state(history, message)
        states.append(state)
        history.append({"sender_type": "customer", "message_content": message})
    return states


def test_cctv_request_then_continuation():
    states = _turns(
        "Necesito instalar un sistema CCTV para mi negocio.",
        "Quiero cubrir la entrada y el almacén.",
        "¿Qué cámaras recomiendas?",
    )
    assert states[0]["state"] == "GOAL_REQUEST"
    assert states[0]["active_problem"] is None
    assert states[1]["active_problem"] is None
    assert states[2]["active_problem"] is None
    assert states[2]["active_goal"] == "REQUEST_SERVICE"


def test_windows_server_vm_same_problem_continuity():
    states = _turns(
        "Mi Windows Server está lento.",
        "La máquina virtual también responde muy lenta.",
        "El problema sigue siendo el rendimiento del servidor.",
    )
    assert states[0]["active_category"] == "performance"
    assert states[1]["active_category"] == "performance"
    assert states[2]["active_category"] == "performance"
    assert states[2]["active_goal"] == "SOLVE_PROBLEM"


def test_notebook_slow_continuity():
    states = _turns(
        "Mi notebook está lento.",
        "Se congela cuando abro varias aplicaciones.",
        "También tarda mucho en iniciar Windows.",
    )
    assert states[0]["active_category"] == "performance"
    assert states[1]["active_category"] == "performance"
    assert states[2]["active_category"] == "performance"
    assert all(s["active_goal"] == "SOLVE_PROBLEM" for s in states)


def test_phone_slow_then_new_problem():
    states = _turns(
        "Mi celular está lento.",
        "Sigue lento cuando abro aplicaciones.",
        "Ahora el celular no carga la batería.",
    )
    assert states[0]["active_category"] == "performance"
    assert states[1]["active_category"] == "performance"
    assert states[2]["active_category"] == "power"
    assert states[2]["state"] == "NEW_PROBLEM"
    assert states[2]["active_problem"] != states[1]["active_problem"]


def test_object_mention_does_not_invent_problem():
    states = _turns(
        "Tengo un notebook Dell.",
        "También tengo un celular Samsung.",
    )
    for state in states:
        assert state["active_problem"] is None
        assert state["active_category"] is None


def test_unrelated_object_request_does_not_inherit_old_problem():
    states = _turns(
        "Mi celular está lento.",
        "También necesito instalar un CCTV.",
    )
    assert states[0]["active_category"] == "performance"
    assert states[1]["state"] == "GOAL_REQUEST"
    assert states[1]["active_goal"] == "REQUEST_SERVICE"


def test_broken_phone_screen_dialogue_preserves_goal_and_problem():
    """Regression for the reported bug: 'Redmi 9A' must not become connectivity."""
    states = _turns(
        "Tengo un movil con pantalla rota deseo arreglarlo.",
        "Redmi 9A deseo saber como se hace para si puedo ser capaz de hacerlo.",
        "¿Puedes pasarme un video de YouTube de como hacerlo?",
        "cambiar la pantalla",
        "redmi 9a",
    )
    assert states[0]["active_category"] == "display"
    assert states[0]["active_problem"] is not None
    # Model/detail turns must not manufacture a connectivity problem.
    assert states[1]["active_category"] != "connectivity"
    assert states[2]["active_category"] != "connectivity"
    assert states[3]["active_category"] == "display"
    assert states[4]["active_category"] != "connectivity"
    assert states[4]["active_problem"] != "problema de conectividad"
