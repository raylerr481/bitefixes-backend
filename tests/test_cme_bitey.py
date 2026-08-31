from app.core.cme_bitey import make_cme_context


def test_bitefixes_identity_is_configuration_not_core_logic():
    ctx = make_cme_context({
        "company_id": "bitefixes",
        "company_name": "BiteFixes",
        "assistant_name": "Bitey",
        "industry": "technical_support",
    })
    assert ctx.assistant_identity == "Bitey"
    assert ctx.tenant_key == "bitefixes"
    assert ctx.research_context(problem="broken screen", model="Redmi 9A")["model"] == "Redmi 9A"


def test_second_company_uses_same_cognitive_context_shape():
    ctx = make_cme_context({
        "company_id": "company-2",
        "company_name": "DentalPlus",
        "assistant_name": "Denti",
        "industry": "dental",
        "currency": "BRL",
    })
    research = ctx.research_context(problem="appointment information")
    assert research["assistant_name"] == "Denti"
    assert research["company_name"] == "DentalPlus"
    assert research["industry"] == "dental"
    assert research["problem"] == "appointment information"


def test_tenants_are_isolated():
    a = make_cme_context({"company_id": "a", "company_name": "A", "assistant_name": "AIA"})
    b = make_cme_context({"company_id": "b", "company_name": "B", "assistant_name": "BIA"})
    assert a.tenant_key != b.tenant_key
    assert a.assistant_identity != b.assistant_identity
    assert a.research_context(problem="private A")["company_id"] == "a"
    assert b.research_context(problem="private B")["company_id"] == "b"


def test_missing_identity_is_rejected():
    try:
        make_cme_context({"company_id": "x", "company_name": "X"})
    except ValueError as exc:
        assert "assistant_name" in str(exc)
    else:
        raise AssertionError("missing assistant identity must be rejected")
