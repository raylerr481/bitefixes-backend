import asyncio
from types import SimpleNamespace

from app.ai.ai_council import _ask_provider
from app.cognitive.context_bridge import build_cognitive_context


class FakeProvider:
    def __init__(self, answer):
        self.answer = answer

    async def generate(self, prompt):
        return self.answer


def make_spec(answer="Respuesta candidata"):
    return SimpleNamespace(
        name="fake-provider",
        provider=FakeProvider(answer),
        cost_class="free",
        capabilities=("general_reasoning",),
    )


def test_cctv_followup_preserves_active_service():
    state = build_cognitive_context(
        message="vivienda, 2 cámaras, una afuera y otra adentro",
        memory={"active_problem": {"intent": "cctv_installation", "goal": "prepare_quote"}, "questions_asked": ["property_type", "camera_count"]},
        current={"entities": {"property_type": "residential", "camera_count": 2, "placement": ["outdoor", "indoor"]}},
    )
    assert state["active_problem"]["intent"] == "cctv_installation"
    assert state["known"]["camera_count"] == 2


def test_windows_server_vm_followup_preserves_goal():
    state = build_cognitive_context(
        message="una máquina virtual",
        memory={"active_problem": {"intent": "windows_server_deployment", "goal": "create_server"}, "questions_asked": ["deployment_type"]},
        current={"entities": {"deployment_type": "virtual_machine"}},
    )
    assert state["active_problem"]["intent"] == "windows_server_deployment"
    assert state["active_problem"]["goal"] == "create_server"
    assert state["known"]["deployment_type"] == "virtual_machine"


def test_notebook_followup_keeps_problem_while_collecting_data():
    state = build_cognitive_context(
        message="es mi notebook de trabajo y tiene SSD",
        memory={"active_problem": {"intent": "upgrade_hardware", "goal": "diagnose_slow_notebook"}},
        current={"entities": {"device": "notebook", "storage": "SSD"}},
    )
    assert state["active_problem"]["intent"] == "upgrade_hardware"
    assert state["known"]["device"] == "notebook"
    assert state["known"]["storage"] == "SSD"


def test_cellphone_new_problem_replaces_active_problem_only_when_explicit():
    state = build_cognitive_context(
        message="ahora el celular tiene la pantalla rota",
        memory={"active_problem": {"intent": "mobile_slow", "goal": "diagnose"}},
        current={"problem": {"intent": "mobile_screen_damage"}},
        identity={"state": "NEW_PROBLEM", "is_new": True},
    )
    assert state["active_problem"]["intent"] == "mobile_screen_damage"


def test_ai_council_output_is_intercepted_as_candidate_not_state_fact(monkeypatch):
    async def fake_health(_spec):
        return {"ok": True}

    monkeypatch.setattr("app.ai.ai_council.resolve_context", lambda **kwargs: {"intent": "windows_server_deployment"})
    monkeypatch.setattr("app.ai.ai_council.contextual_directive", lambda state: "continue active goal")
    monkeypatch.setattr("app.ai.ai_council._search_context", lambda *args: {})
    monkeypatch.setattr("app.ai.ai_council._business_index", lambda *args: {"services": []})
    monkeypatch.setattr("app.ai.ai_council.probe_provider_spec", fake_health)

    result = asyncio.run(_ask_provider(
        make_spec("Probablemente será una plataforma empresarial de IA."),
        "una máquina virtual",
        "es",
        {"memory": {"active_problem": {"intent": "windows_server_deployment"}}, "business_context": {}, "intent": {}},
    ))

    assert result["answer"] == "Probablemente será una plataforma empresarial de IA."
    assert result["evidence_guard"]["state_update_allowed"] is False
    assert result["evidence_guard"]["llm_answer_is_fact"] is False
    assert result["evidence_guard"]["canonical_facts"] == []
