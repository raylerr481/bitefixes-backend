from app.services.concept_engine import understand, normalize_text, propose_learning


def test_normalizes_accents_and_spacing():
    assert normalize_text("  Câmeras   de segurança! ") == "cameras de seguranca"


def test_understands_category_without_manual_intent_rule():
    result = understand("celulares")
    assert result["known"] is True
    assert result["concept"]["concept"] == "mobile_device"
    assert "mobile_repair" in result["concept"]["diagnostic_signals"]


def test_understands_typo_and_colloquial_bootloop():
    result = understand("meu telefone está bootloopando")
    assert result["known"] is True
    assert result["concept"]["concept"] == "boot_loop"


def test_unknown_is_candidate_not_fake_knowledge():
    result = propose_learning("mi celular hace una cosa totalmente nueva", intent=None, language="es")
    assert result["status"] == "candidate"
    assert result["requires_validation"] is True
    assert result["validated"] is False
