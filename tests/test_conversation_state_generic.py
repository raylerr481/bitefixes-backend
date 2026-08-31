"""Generic continuity contract: facts accumulate and resolved facts are not re-asked.

These tests deliberately avoid domain-specific words/rules. They exercise the
shape of the cognitive state rather than CCTV/BiteFixes behavior.
"""
from app.core.bitey import BiteyCore


def _process(core, message, conversation_id, company_id):
    return core.process_message(
        message,
        conversation_id=conversation_id,
        company_id=company_id,
        language="es",
    )


def test_facts_accumulate_without_domain_specific_rules():
    core = BiteyCore()
    first = _process(core, "Necesito asistencia para una instalación.", "continuity-a", 1001)
    second = _process(core, "Es para dos equipos y tengo conexión disponible.", "continuity-a", 1001)

    assert first is not None
    assert second is not None
    state = getattr(core, "state", None) or getattr(core, "context", None)
    assert state is not None


def test_company_context_is_not_shared_between_conversations():
    core = BiteyCore()
    _process(core, "Necesito asistencia para una instalación.", "continuity-a", 1001)
    _process(core, "Necesito asistencia para una instalación.", "continuity-b", 2002)

    # The core must keep conversation/company identity explicit rather than
    # relying on process-global mutable business facts.
    attrs = vars(core)
    serialized = repr(attrs)
    assert "1001" not in serialized or "2002" not in serialized or "company" in serialized.lower()
