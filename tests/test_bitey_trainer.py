from app.services.bitey_trainer_service import evaluate_responses, build_training_plan, human_task_policy


def test_trainer_evaluates_candidates():
    result = evaluate_responses("Explain AI", [{"provider": "a", "response": "AI is software."}, {"provider": "b", "response": "AI systems learn patterns from data and can generate or classify information. They require evaluation and safeguards."}])
    assert result["trainer"] == "bitey-trainer"
    assert result["best_candidate"]["provider"] == "b"
    assert result["promotion"] == "advisory_only"


def test_trainer_builds_learning_plan():
    result = build_training_plan(company="Acme", domain="AI", needs=["improve support assistant"])
    assert result["status"] == "ready"
    assert "reasoner" in result["roles"]
    assert "contradiction_check" in result["checks"]
    assert result["promotion_rule"]


def test_human_tasks_require_approval():
    policy = human_task_policy()
    assert policy["approval_required"] is True
    assert "identity verification" in policy["human_required"]
