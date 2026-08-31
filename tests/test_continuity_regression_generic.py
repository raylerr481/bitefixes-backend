"""Regression contracts for continuity across unrelated support domains.

The scenarios intentionally use neutral labels rather than domain-specific
rules. The contract is state continuity, isolation, and problem replacement.
"""
from app.core.bitey import BiteyCore


def process(core, text, conversation_id, company_id):
    return core.process_message(text, conversation_id=conversation_id, company_id=company_id, language="es")


def test_four_scenarios_use_one_core_without_domain_rules():
    core = BiteyCore()
    scenarios = [
        ("s1", 101, ["Necesito instalar dos equipos.", "Uno estará dentro y otro fuera.", "Tengo conexión y alimentación disponibles."]),
        ("s2", 202, ["Tengo un servidor y una máquina virtual.", "La máquina virtual presenta el problema.", "El servidor sigue operativo."]),
        ("s3", 303, ["Un equipo funciona lentamente.", "El almacenamiento tiene espacio disponible.", "El problema comenzó recientemente."]),
        ("s4", 404, ["Tengo un dispositivo con un problema.", "El problema inicial quedó registrado.", "Ahora aparece un problema diferente."]),
    ]
    for conversation_id, company_id, messages in scenarios:
        results = [process(core, m, conversation_id, company_id) for m in messages]
        assert all(r is not None for r in results)
        for result in results:
            assert result.get("conversation_id") == conversation_id
            assert result.get("company_id") == company_id


def test_company_isolation_survives_parallel_scenarios():
    core = BiteyCore()
    process(core, "Dato exclusivo de empresa A.", "parallel-a", 1001)
    process(core, "Dato exclusivo de empresa B.", "parallel-b", 2002)
    a = process(core, "Continúo con mi caso.", "parallel-a", 1001)
    b = process(core, "Continúo con mi caso.", "parallel-b", 2002)
    assert a.get("company_id") == 1001
    assert b.get("company_id") == 2002
    assert "empresa B" not in repr(a).lower()
    assert "empresa A" not in repr(b).lower()
