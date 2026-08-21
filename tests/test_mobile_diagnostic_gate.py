from app.services.workflows import mobile_repair


def test_broken_phone_starts_diagnosis_without_ticket():
    result = mobile_repair.execute("tengo telefono roto", language="es")
    assert result["success"] is False
    assert result["diagnostic_pending"] is True
    assert result["metadata"]["issue_type"] is None


def test_diagnostic_request_never_creates_ticket():
    result = mobile_repair.execute("realiza el diagnostico", language="es")
    assert result["success"] is False
    assert result["diagnostic_pending"] is True


def test_explicit_screen_repair_request_can_progress():
    result = mobile_repair.execute(
        "quiero reparar la pantalla rota y necesito presupuesto", language="es"
    )
    assert result["success"] is True
    assert result["diagnostic_pending"] is False
    assert result["metadata"]["issue_type"] == "screen"
