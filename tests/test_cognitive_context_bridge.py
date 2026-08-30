from app.cognitive.context_bridge import build_cognitive_context, merge_context


def test_merge_does_not_erase_context_with_empty_values():
    merged = merge_context(
        {"intent": "cctv_installation", "entities": {"camera_count": 2}},
        {"intent": "", "entities": {"placement": ["indoor", "outdoor"]}},
    )
    assert merged["intent"] == "cctv_installation"
    assert merged["entities"]["camera_count"] == 2
    assert merged["entities"]["placement"] == ["indoor", "outdoor"]


def test_followup_keeps_active_problem_and_accumulates_answers():
    context = build_cognitive_context(
        message="vivienda, 2 cámaras, una afuera y otra adentro",
        memory={
            "active_problem": {"intent": "cctv_installation", "goal": "prepare_quote"},
            "questions_asked": ["property_type", "camera_count", "placement"],
        },
        current={
            "entities": {
                "property_type": "residential",
                "camera_count": 2,
                "placement": ["outdoor", "indoor"],
            }
        },
        identity={"state": "CONTINUATION", "is_new": False},
        business={"services": [{"id": 5, "name": "CCTV Installation"}]},
    )
    assert context["active_problem"]["intent"] == "cctv_installation"
    assert context["active_problem"]["goal"] == "prepare_quote"
    assert context["active_problem"]["state"] == "CONTINUATION"
    assert context["known"]["camera_count"] == 2
    assert context["known"]["property_type"] == "residential"


def test_new_problem_can_replace_active_problem_when_identity_says_new():
    context = build_cognitive_context(
        message="ahora la pantalla está rota",
        memory={"active_problem": {"intent": "mobile_slow", "goal": "diagnose"}},
        current={"problem": {"intent": "screen_damage"}},
        identity={"state": "NEW_PROBLEM", "is_new": True},
    )
    assert context["active_problem"]["intent"] == "screen_damage"
    assert context["active_problem"]["state"] == "NEW_PROBLEM"
