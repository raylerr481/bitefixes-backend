from app.ai.apprentice import (
    build_learning_context,
    build_training_record,
    evaluate_bitey,
    provider_role,
)


def test_external_models_have_training_roles():
    assert provider_role("groq") == "director"
    assert provider_role("deepseek-free") == "specialist"
    assert provider_role("qwen-free") == "reviewer"
    assert provider_role("unknown") == "advisor"


def test_shared_context_contains_bitefixes_sources_without_granting_write_authority():
    context = build_learning_context(
        user_message="mi notebook esta lento",
        website_context={"services": ["hardware_upgrade"]},
        backend_context={"customer": {"id": 7}, "open_tickets": []},
        conversation_context=[{"role": "user", "content": "mi notebook esta lento"}],
    )
    assert context["learning_mode"] == "apprentice"
    assert context["bitey_status"] == "student"
    assert context["sources"]["website"]["services"] == ["hardware_upgrade"]
    assert context["sources"]["bitefixes_backend"]["customer"]["id"] == 7
    assert context["write_policy"] == "providers_propose_bitey_validates"


def test_bitey_stays_in_training_until_all_required_dimensions_are_strong():
    result = evaluate_bitey(
        capability_scores={
            "context_use": 0.95,
            "source_alignment": 0.94,
            "problem_understanding": 0.93,
            "action_quality": 0.91,
            "verification": 0.60,
        }
    )
    assert result["status"] == "training"
    assert result["authority_granted"] is False
    assert result["recommendation"] == "continue_training"


def test_bitey_can_be_recommended_for_graduation_but_never_receives_authority_automatically():
    result = evaluate_bitey(
        capability_scores={
            "context_use": 0.95,
            "source_alignment": 0.94,
            "problem_understanding": 0.93,
            "action_quality": 0.91,
            "verification": 0.90,
        }
    )
    assert result["status"] == "ready"
    assert result["recommendation"] == "candidate_for_graduation"
    assert result["authority_granted"] is False


def test_training_record_is_auditable_and_proposal_only():
    record = build_training_record(
        user_message="wifi se desconecta",
        provider_results=[
            {"provider": "groq", "status": "ok"},
            {"provider": "deepseek-free", "status": "ok"},
        ],
        selected={"provider": "deepseek-free"},
        evaluation={"status": "training"},
    )
    assert record["mode"] == "apprentice"
    assert record["providers"][0]["role"] == "director"
    assert record["providers"][1]["role"] == "specialist"
    assert record["selected_provider"] == "deepseek-free"
    assert record["next_step"] == "persist_after_core_validation"
