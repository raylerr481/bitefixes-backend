from app.cognitive.evidence_guard import guard_state_update, partition_claims


def test_llm_claim_is_hypothesis_not_fact():
    parts = partition_claims([
        {"key": "deployment_type", "value": "vm", "source": "user"},
        {"key": "workload", "value": "AI system", "source": "llm"},
    ])
    assert len(parts["facts"]) == 1
    assert parts["facts"][0]["key"] == "deployment_type"
    assert parts["hypotheses"][0]["key"] == "workload"


def test_unsupported_llm_fact_cannot_enter_canonical_state():
    state = {"goal": "windows_server", "deployment_type": "vm"}
    proposed = {
        "goal": "windows_server",
        "deployment_type": "vm",
        "workload": "enterprise AI platform",
    }
    result = guard_state_update(
        state,
        proposed,
        evidence=[{"key": "deployment_type", "value": "vm", "source": "user"}],
    )
    assert result["goal"] == "windows_server"
    assert result["deployment_type"] == "vm"
    assert "workload" not in result


def test_verified_evidence_can_update_existing_fact():
    state = {"goal": "windows_server", "deployment_type": "physical"}
    result = guard_state_update(
        state,
        {"deployment_type": "virtual_machine"},
        evidence=[{"key": "deployment_type", "value": "virtual_machine", "source": "user", "verified": True}],
    )
    assert result["deployment_type"] == "virtual_machine"
