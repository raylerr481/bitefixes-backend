"""Deterministic Bitey Core fallback.

This is the last-resort local reasoning layer. It never replaces Groq or
OpenRouter Free when either provider returns a usable answer. Its purpose is
to keep continuity and provide useful, bounded next steps when external AI is
unavailable. Enterprise context is only used when the conversation is clearly
business/service related.
"""
from __future__ import annotations

from typing import Any, Dict


def _text(value: Any) -> str:
    return str(value or "").strip().lower()


def _is_business_context_relevant(message: str, context: Dict[str, Any]) -> bool:
    """Apply company context only when the user is actually in that scope."""
    m = _text(message)
    state = context.get("contextual_state") or {}
    problem = context.get("conversation_problem") or {}
    business_markers = (
        "bitefix", "empresa", "empresa", "servicio", "presupuesto", "cotización", "cotizacion",
        "ticket", "cliente", "técnico", "tecnico", "reparar", "reparación", "reparacion",
        "instalar", "impresora", "computadora", "ordenador", "pc", "laptop", "notebook",
        "celular", "móvil", "movil", "cctv", "cámara", "camara", "wifi", "red",
    )
    if any(marker in m for marker in business_markers):
        return True
    return bool(state.get("active_problem") or problem.get("active_problem"))


def _active_problem(context: Dict[str, Any]) -> Dict[str, Any]:
    state = context.get("contextual_state") or {}
    problem = context.get("conversation_problem") or {}
    merged = dict(problem)
    for key, value in state.items():
        if value not in (None, "", [], {}):
            merged[key] = value
    return merged


def fallback_answer(message: str, *, language: str = "es", context: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    """Return a useful local answer for bounded, recognizable situations."""
    context = context or {}
    m = _text(message)
    lang = _text(language) or "es"
    business_relevant = _is_business_context_relevant(message, context)
    problem = _active_problem(context)
    category = _text(problem.get("category"))
    entities = problem.get("entities") if isinstance(problem.get("entities"), dict) else {}
    device = _text(problem.get("device") or problem.get("device_kind"))
    symptoms = " ".join(_text(v) for v in entities.values() if isinstance(v, (str, int)))
    combined = f"{m} {category} {device} {symptoms}"

    # Focused local diagnostic: desktop/PC with no power signs.
    no_power = any(x in combined for x in ("no enciende", "no enciende ninguna luz", "ninguna luz", "no hace ningún ruido", "no hace ningun ruido", "no prende"))
    pc = any(x in combined for x in ("pc", "computadora", "ordenador", "desktop", "escritorio"))
    if no_power and pc:
        if lang.startswith("pt"):
            answer = ("Entendido. Ya sabemos que es una computadora de escritorio y que no hay luces ni sonido. "
                      "No voy a repetir esas preguntas. Primero confirma solo esto: ¿el cable de alimentación está conectado firmemente a la PC y a la toma? Si puedes, prueba otra toma. "
                      "No abras la fuente de alimentación todavía.")
        elif lang.startswith("en"):
            answer = ("Understood. We already know it is a desktop PC with no lights and no sound, so I won't repeat those questions. "
                      "First, confirm only this: is the power cable firmly connected to the PC and the outlet? If possible, test another outlet. "
                      "Do not open the power supply yet.")
        else:
            answer = ("Entendido. Ya sabemos que es una computadora de escritorio y que no hay ninguna luz ni sonido. "
                      "No voy a repetir esas preguntas. Primero confirma solo esto: ¿el cable de alimentación está bien conectado a la PC y al tomacorriente? Si puedes, prueba otro tomacorriente. "
                      "Todavía no abras la fuente de alimentación.")
        return {"answer": answer, "provider": "bitey-core-local", "mode": "bounded_diagnostic", "business_context_applied": business_relevant}

    # Generic local continuity fallback: preserve an established problem and ask one useful next question.
    if problem.get("active_problem") or problem.get("category"):
        if lang.startswith("pt"):
            answer = "Vou manter o problema já identificado e avançar sem reiniciar o diagnóstico. Qual é o sintoma mais importante que ainda não verificamos?"
        elif lang.startswith("en"):
            answer = "I'll keep the problem already identified and continue without restarting the diagnosis. What is the most important symptom we have not checked yet?"
        else:
            answer = "Mantendré el problema ya identificado y continuaré sin reiniciar el diagnóstico. ¿Cuál es el síntoma más importante que todavía no hemos comprobado?"
        return {"answer": answer, "provider": "bitey-core-local", "mode": "continuity_fallback", "business_context_applied": business_relevant}

    return None
