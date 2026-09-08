"""Deterministic Bitey Core fallback and bounded diagnostic guard."""
from __future__ import annotations
from typing import Any, Dict


def _text(value: Any) -> str:
    return str(value or "").strip().lower()


def _active_problem(context: Dict[str, Any]) -> Dict[str, Any]:
    state = context.get("contextual_state") or {}
    problem = context.get("conversation_problem") or {}
    merged = dict(problem) if isinstance(problem, dict) else {}
    for key, value in state.items():
        if value not in (None, "", [], {}):
            merged[key] = value
    return merged


def _business_context_relevant(message: str, context: Dict[str, Any]) -> bool:
    m = _text(message)
    markers = ("bitefix", "empresa", "servicio", "presupuesto", "cotización", "cotizacion", "ticket", "cliente", "técnico", "tecnico", "reparar", "reparación", "reparacion", "instalar", "impresora", "computadora", "ordenador", "pc", "laptop", "notebook", "celular", "móvil", "movil", "cctv", "cámara", "camara", "wifi", "red")
    return any(marker in m for marker in markers) or bool(_active_problem(context).get("active_problem"))


def _known_no_power(problem: Dict[str, Any], message: str) -> bool:
    combined = " ".join([_text(message), _text(problem.get("active_problem")), _text(problem.get("category")), _text(problem.get("device")), _text(problem.get("device_kind"))])
    entities = problem.get("entities") if isinstance(problem.get("entities"), dict) else {}
    combined += " " + " ".join(_text(v) for v in entities.values() if isinstance(v, (str, int)))
    no_power = any(x in combined for x in ("no enciende", "no enciende ninguna luz", "ninguna luz", "no hace ningún ruido", "no hace ningun ruido", "no prende"))
    pc = any(x in combined for x in ("pc", "computadora", "ordenador", "desktop", "escritorio", "computer"))
    return no_power and pc


def bounded_diagnostic_answer(message: str, *, language: str = "es", context: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    """Return the next deterministic diagnostic step when the state is unambiguous."""
    context = context or {}
    problem = _active_problem(context)
    if not _known_no_power(problem, message):
        return None
    lang = _text(language) or "es"
    if lang.startswith("pt"):
        answer = ("Entendido. Já sabemos que é um computador de mesa, Windows, sem luzes e sem nenhum ruído. "
                  "Não vou repetir esses dados. Vamos avançar no diagnóstico: o cabo de alimentação está firmemente conectado ao computador e à tomada? Se puder, teste outra tomada. "
                  "Ainda não abra a fonte de alimentação.")
    elif lang.startswith("en"):
        answer = ("Understood. We already know it is a desktop PC running Windows, with no lights and no sound. "
                  "I won't repeat those facts. Let's advance the diagnosis: is the power cable firmly connected to the PC and the outlet? If possible, test another outlet. "
                  "Do not open the power supply yet.")
    else:
        answer = ("Entendido. Ya sabemos que es una computadora de escritorio, Windows, sin ninguna luz y sin ningún ruido. "
                  "No voy a repetir esos datos. Avancemos con el diagnóstico: ¿el cable de alimentación está firmemente conectado a la PC y al tomacorriente? Si puedes, prueba otro tomacorriente. "
                  "Todavía no abras la fuente de alimentación.")
    return {"answer": answer, "provider": "bitey-core-diagnostic-guard", "mode": "bounded_diagnostic", "business_context_applied": _business_context_relevant(message, context)}


def fallback_answer(message: str, *, language: str = "es", context: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    """Last-resort local reasoning. External AI remains authoritative when usable."""
    context = context or {}
    bounded = bounded_diagnostic_answer(message, language=language, context=context)
    if bounded:
        return bounded
    problem = _active_problem(context)
    lang = _text(language) or "es"
    if problem.get("active_problem") or problem.get("category"):
        if lang.startswith("pt"):
            answer = "Vou manter o problema já identificado e avançar sem reiniciar o diagnóstico. Qual é o sintoma mais importante que ainda não verificamos?"
        elif lang.startswith("en"):
            answer = "I'll keep the problem already identified and continue without restarting the diagnosis. What is the most important symptom we have not checked yet?"
        else:
            answer = "Mantendré el problema ya identificado y continuaré sin reiniciar el diagnóstico. ¿Cuál es el síntoma más importante que todavía no hemos comprobado?"
        return {"answer": answer, "provider": "bitey-core-local", "mode": "continuity_fallback", "business_context_applied": _business_context_relevant(message, context)}
    return None
