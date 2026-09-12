"""Deterministic Bitey Core fallback and bounded diagnostic guard."""
from __future__ import annotations
from typing import Any, Dict


def _text(value: Any) -> str:
    return str(value or "").strip().lower()


def _history_text(context: Dict[str, Any]) -> str:
    history = context.get("history") or []
    parts = []
    if isinstance(history, list):
        for item in history[-12:]:
            if isinstance(item, dict):
                role = _text(item.get("role") or item.get("sender_type"))
                content = _text(item.get("content") or item.get("message") or item.get("text") or item.get("message_content") or item.get("ai_response"))
                if content:
                    parts.append(f"{role}: {content}")
            else:
                parts.append(_text(item))
    return " ".join(p for p in parts if p)


def _user_history_text(context: Dict[str, Any]) -> str:
    history = context.get("history") or []
    parts = []
    if isinstance(history, list):
        for item in history[-12:]:
            if not isinstance(item, dict):
                continue
            role = _text(item.get("role") or item.get("sender_type"))
            if role in {"user", "customer"}:
                content = _text(item.get("content") or item.get("message") or item.get("text") or item.get("message_content"))
                if content:
                    parts.append(content)
    return " ".join(parts)


def _active_problem(context: Dict[str, Any]) -> Dict[str, Any]:
    state = context.get("contextual_state") or {}
    problem = context.get("conversation_problem") or {}
    merged = dict(problem) if isinstance(problem, dict) else {}
    for key, value in state.items():
        if value not in (None, "", [], {}):
            merged[key] = value
    history = _history_text(context)
    if history:
        merged["history_text"] = history
    return merged


def _business_context_relevant(message: str, context: Dict[str, Any]) -> bool:
    m = _text(message)
    markers = ("bitefix", "empresa", "servicio", "presupuesto", "cotización", "cotizacion", "ticket", "cliente", "técnico", "tecnico", "reparar", "reparación", "reparacion", "instalar", "impresora", "computadora", "ordenador", "pc", "laptop", "notebook", "celular", "móvil", "movil", "cctv", "cámara", "camara", "wifi", "red")
    return any(marker in m for marker in markers) or bool(_active_problem(context).get("active_problem"))


def _known_no_power(problem: Dict[str, Any], message: str) -> bool:
    combined = " ".join([
        _text(message),
        _text(problem.get("active_problem")),
        _text(problem.get("category")),
        _text(problem.get("device")),
        _text(problem.get("device_kind")),
        _text(problem.get("history_text")),
    ])
    entities = problem.get("entities") if isinstance(problem.get("entities"), dict) else {}
    combined += " " + " ".join(_text(v) for v in entities.values() if isinstance(v, (str, int)))
    no_power = any(x in combined for x in ("no enciende", "no prende", "no arranca", "no inicia"))
    pc = any(x in combined for x in ("pc", "computadora", "ordenador", "desktop", "escritorio", "computer"))
    return no_power and pc


def _user_power_facts(context: Dict[str, Any]) -> tuple[bool, bool, bool, bool]:
    """Return confirmed light/no-light and noise/no-noise facts from user turns only."""
    user_text = _user_history_text(context)
    light_yes = any(x in user_text for x in (
        "se enciende una luz", "se enciende la luz", "se prende una luz", "se prende la luz",
        "hay una luz", "hay luz", "una luz encendida", "luz encendida", "led encendido",
    ))
    light_no = any(x in user_text for x in (
        "ninguna luz", "sin ninguna luz", "sin luz", "no hay luz", "no prende ninguna luz",
        "no enciende ninguna luz", "no se enciende ninguna luz", "no se prende ninguna luz",
    ))
    noise_yes = any(x in user_text for x in (
        "se escucha un ruido", "escucho un ruido", "hay ruido", "hace ruido", "se escucha ruido",
        "se oye un ruido", "oigo un ruido", "se escucha un sonido", "hay sonido",
    ))
    noise_no = any(x in user_text for x in (
        "ningún ruido", "ningun ruido", "sin ruido", "no hace ruido", "no hace ningún ruido",
        "no hace ningun ruido", "no se escucha ningún ruido", "no se escucha ningun ruido",
        "no escucho ningún ruido", "no escucho ningun ruido", "no se escucha ruido",
    ))
    return light_yes, light_no, noise_yes, noise_no


def bounded_diagnostic_answer(message: str, *, language: str = "es", context: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    """Return a safe deterministic diagnostic step when the state is unambiguous."""
    context = context or {}
    problem = _active_problem(context)
    if not _known_no_power(problem, message):
        return None
    light_yes, light_no, noise_yes, noise_no = _user_power_facts(context)
    lang = _text(language) or "es"

    # Never infer facts from Bitey's own previous questions or answers.
    if lang.startswith("pt"):
        if not (light_yes or light_no):
            answer = "Entendido. Já sabemos que é um computador de mesa e que ele não liga. Não vou assumir se há luzes ou ruídos. Ao pressionar o botão de ligar, alguma luz acende?"
        elif not (noise_yes or noise_no):
            light_state = "há uma luz indicadora acesa" if light_yes else "não há luzes indicadoras"
            answer = f"Entendido. Já confirmamos que {light_state}. Sem assumir outros sintomas: ao pressionar o botão de ligar, você ouve algum ruído, como ventilador ou clique?"
        elif light_yes and noise_no:
            answer = "Entendido. Já confirmamos que há uma luz indicadora, mas nenhum ruído e nenhum ventilador gira. O cabo de alimentação está firmemente conectado à PC e à tomada? Se puder, teste outra tomada. Não abra a fonte de alimentação."
        elif light_no and noise_no:
            answer = "Entendido. Já confirmamos que não há luzes, não há ruído e nenhum ventilador gira. O cabo de alimentação está firmemente conectado à PC e à tomada? Se puder, teste outra tomada. Não abra a fonte de alimentação."
        else:
            answer = "Entendido. Já temos os sintomas básicos confirmados. O cabo de alimentação está firmemente conectado à PC e à tomada? Se puder, teste outra tomada. Não abra a fonte de alimentação."
    elif lang.startswith("en"):
        if not (light_yes or light_no):
            answer = "Understood. We know it is a desktop PC and that it does not turn on. I will not assume whether there are lights or sounds. When you press the power button, does any light come on?"
        elif not (noise_yes or noise_no):
            light_state = "there is an indicator light on" if light_yes else "there are no indicator lights"
            answer = f"Understood. We have confirmed that {light_state}. Without assuming other symptoms: when you press the power button, do you hear any sound, such as a fan or click?"
        elif light_yes and noise_no:
            answer = "Understood. We have confirmed an indicator light, but no sound and no fan movement. Is the power cable firmly connected to the PC and the outlet? If possible, test another outlet. Do not open the power supply."
        elif light_no and noise_no:
            answer = "Understood. We have confirmed no lights, no sound and no fan movement. Is the power cable firmly connected to the PC and the outlet? If possible, test another outlet. Do not open the power supply."
        else:
            answer = "Understood. We have confirmed the basic symptoms. Is the power cable firmly connected to the PC and the outlet? If possible, test another outlet. Do not open the power supply."
    else:
        if not (light_yes or light_no):
            answer = "Entendido. Ya sabemos que es una PC de escritorio y que no enciende. No voy a asumir si hay luces o ruidos. Al presionar el botón de encendido, ¿se enciende alguna luz?"
        elif not (noise_yes or noise_no):
            light_state = "hay una luz indicadora encendida" if light_yes else "no hay luces indicadoras"
            answer = f"Entendido. Ya confirmamos que {light_state}. Sin asumir otros síntomas: al presionar el botón de encendido, ¿escuchas algún ruido, como un ventilador o un clic?"
        elif light_yes and noise_no:
            answer = "Entendido. Ya confirmamos que hay una luz indicadora, pero no hay ruido y ningún ventilador gira. ¿El cable de alimentación está firmemente conectado a la PC y al tomacorriente? Si puedes, prueba otro tomacorriente. No abras todavía la fuente de alimentación."
        elif light_no and noise_no:
            answer = "Entendido. Ya confirmamos que no hay luces, no hay ruido y ningún ventilador gira. ¿El cable de alimentación está firmemente conectado a la PC y al tomacorriente? Si puedes, prueba otro tomacorriente. No abras todavía la fuente de alimentación."
        else:
            answer = "Entendido. Ya tenemos confirmados los síntomas básicos. ¿El cable de alimentación está firmemente conectado a la PC y al tomacorriente? Si puedes, prueba otro tomacorriente. No abras todavía la fuente de alimentación."
    return {"answer": answer, "provider": "bitey-core-diagnostic-guard", "mode": "bounded_diagnostic", "business_context_applied": _business_context_relevant(message, context)}


def fallback_answer(message: str, *, language: str = "es", context: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    """Last-resort local reasoning. External AI remains authoritative when usable."""
    context = context or {}
    bounded = bounded_diagnostic_answer(message, language=language, context=context)
    if bounded:
        return bounded
    problem = _active_problem(context)
    lang = _text(language) or "es"
    if problem.get("active_problem") or problem.get("category") or problem.get("history_text"):
        if lang.startswith("pt"):
            answer = "Vou manter o problema já identificado e avançar sem reiniciar o diagnóstico. Qual é o sintoma mais importante que ainda não verificamos?"
        elif lang.startswith("en"):
            answer = "I'll keep the problem already identified and continue without restarting the diagnosis. What is the most important symptom we have not checked yet?"
        else:
            answer = "Mantendré el problema ya identificado y continuaré sin reiniciar el diagnóstico. ¿Cuál es el síntoma más importante que todavía no hemos comprobado?"
        return {"answer": answer, "provider": "bitey-core-local", "mode": "continuity_fallback", "business_context_applied": _business_context_relevant(message, context)}
    return None
