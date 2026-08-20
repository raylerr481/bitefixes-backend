from app.core.bitey import _inherit_active_intent, _is_greeting
from app.services.decision_engine import _is_contextual_followup, _is_mobile_category, _business_location


def test_greeting_does_not_inherit_active_intent():
    context = {"last_intent": "mobile_repair", "last_confidence": 0.96}
    result = _inherit_active_intent({"intent": None, "confidence": 0}, context, "hola")
    assert result.get("intent") is None
    assert _is_greeting("holla") is False


def test_contextual_mobile_followup_inherits_intent():
    context = {"last_intent": "mobile_repair", "last_confidence": 0.96}
    result = _inherit_active_intent({"intent": None, "confidence": 0}, context, "dime como puedo repararlo")
    assert result["intent"] == "mobile_repair"
    assert result["context_inherited"] is True
    assert _is_contextual_followup("dime como puedo repararlo", True)


def test_mobile_category_does_not_open_ticket():
    assert _is_mobile_category("celulares") is True
    assert _is_mobile_category("celulares rotos") is False


def test_location_is_read_from_business_profile():
    context = {"business_profile": {"address": "Rua Central 123"}}
    assert _business_location(context) == "Rua Central 123"


def test_followup_question_is_contextual():
    assert _is_contextual_followup("cuanto cuesta?", True) is True
    assert _is_contextual_followup("donde residen ustedes", True) is True
    assert _is_contextual_followup("quiero instalar camaras", True) is False
