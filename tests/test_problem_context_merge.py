from app.services.problem_identity_service import analyze_problem


def test_windows_version_is_entity_update_of_active_slow_pc():
    first = analyze_problem("tengo mi pc lenta con windows", current_intent="computer_repair")
    assert first["category"] == "slow_performance"
    assert first["device_kind"] == "computer"
    assert first["platform"] == "windows"

    second = analyze_problem(
        "windows 10",
        active_intent=first["intent"],
        active_problem=first["category"],
        active_device=first["device"],
        context={"last_platform": first["platform"]},
    )

    assert second["state"] == "CONTINUATION"
    assert second["is_new"] is False
    assert second["category"] == "slow_performance"
    assert second["device_kind"] == "computer"
    assert second["platform"] == "windows"
    assert second["os_version"] == "Windows 10"
    assert second["entities"]["os_version"] == "Windows 10"


def test_new_mobile_problem_is_not_merged_with_active_computer_problem():
    first = analyze_problem("mi pc está lenta con windows", current_intent="computer_repair")
    second = analyze_problem(
        "mi celular no enciende",
        active_intent=first["intent"],
        active_problem=first["category"],
        active_device=first["device"],
        context={"last_platform": first["platform"]},
    )

    assert second["state"] == "NEW_PROBLEM"
    assert second["is_new"] is True
    assert second["device_kind"] == "mobile"
    assert second["category"] == "power"
