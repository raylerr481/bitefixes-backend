from app.ai.teacher_loop import TeacherLoop


def test_teacher_proposal_is_not_trusted_without_verification():
    loop = TeacherLoop()
    node = loop.learn_from_teacher("wifi_driver", "check the adapter driver", "groq", 0.9)
    assert node.status == "candidate"
    assert node.successes == 0


def test_verified_experience_is_retrievable():
    loop = TeacherLoop()
    loop.record_case("case-1", "computer_repair", ["slow"], "upgrade_ram", "performance improved", True, 0.8)
    loop.record_case("case-2", "computer_repair", ["slow"], "clean_startup", "no improvement", False, 0.6)
    successes = loop.memory.successful("computer_repair", ["slow"])
    failures = loop.memory.failed("computer_repair", ["slow"])
    assert successes[0].action == "upgrade_ram"
    assert failures[0].action == "clean_startup"


def test_two_successful_verifications_can_promote_candidate():
    loop = TeacherLoop()
    loop.learn_from_teacher("screen_damage", "inspect display assembly", "technical_ai", 0.7)
    loop.verify_candidate("screen_damage", True)
    node = loop.verify_candidate("screen_damage", True)
    assert node.status == "trusted"
