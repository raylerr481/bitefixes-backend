"""Bitey Workflow - Mobile Repair.

Diagnostic-first flow: Bitey gathers the minimum information needed before
creating a ticket or promising a repair estimate. External AI may advise, but
this workflow remains deterministic and authoritative for ticket creation.
"""

import re


def _normalize(text: str) -> str:
    text = str(text or "").lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _is_diagnostic_request(text: str) -> bool:
    return any(token in text for token in (
        "diagnostico", "diagnóstico", "diagnosticar", "diagnose", "diagnostic",
        "revisar", "revision", "revisión", "que le pasa", "qué le pasa",
    ))


def _has_repair_or_quote_request(text: str) -> bool:
    return any(token in text for token in (
        "reparar", "arreglar", "consertar", "repair", "presupuesto",
        "orçamento", "orcamento", "precio", "preco", "cotizacion", "cotización",
    ))


def _issue_type(text: str) -> str | None:
    if any(token in text for token in ("pantalla", "tela", "display", "screen")):
        return "screen"
    if any(token in text for token in ("carga", "cargar", "carrega", "carregar", "charger", "charging")):
        return "charging"
    if any(token in text for token in ("bateria", "batería", "battery")):
        return "battery"
    if any(token in text for token in ("no enciende", "no prende", "nao liga", "não liga", "no prende", "doesn't turn on")):
        return "power"
    if any(token in text for token in ("camara", "cámara", "camera")):
        return "camera"
    if any(token in text for token in ("agua", "mojado", "mojada", "liquido", "líquido", "water")):
        return "liquid"
    return None


def _diagnostic_response(issue: str | None, language: str) -> str:
    normalized_language = (language or "es").lower()

    if normalized_language.startswith("pt"):
        if issue == "screen":
            return "Vamos fazer o diagnóstico. A tela está quebrada: o celular liga e o toque funciona normalmente?"
        if issue == "charging":
            return "Vamos fazer o diagnóstico. Ao conectar o carregador, aparece algum sinal de carga ou o aparelho permanece sem carregar?"
        if issue == "battery":
            return "Vamos fazer o diagnóstico. A bateria descarrega rapidamente, incha ou o celular desliga sozinho?"
        if issue == "power":
            return "Vamos fazer o diagnóstico. Ao tentar ligar, o celular vibra, emite som ou mostra algum logotipo?"
        if issue == "liquid":
            return "Vamos fazer o diagnóstico. Quando o celular teve contato com líquido e ele ainda está ligado? Evite carregá-lo até avaliarmos."
        return "Vamos fazer o diagnóstico. O que aconteceu com o celular? Escolha uma opção: tela, não liga, não carrega, bateria, câmera ou outro problema."

    if normalized_language.startswith("en"):
        if issue == "screen":
            return "Let's diagnose it. The screen is damaged: does the phone turn on and does touch still work normally?"
        if issue == "charging":
            return "Let's diagnose it. When you connect the charger, does the phone show any charging indication or does it stay without charging?"
        if issue == "battery":
            return "Let's diagnose it. Does the battery drain quickly, swell, or make the phone shut down unexpectedly?"
        if issue == "power":
            return "Let's diagnose it. When you try to turn it on, does it vibrate, make a sound, or show a logo?"
        if issue == "liquid":
            return "Let's diagnose it. When did the phone contact liquid, and is it still powered on? Avoid charging it until we assess it."
        return "Let's diagnose it. What happened to the phone? Choose: screen, won't turn on, won't charge, battery, camera, or another problem."

    if issue == "screen":
        return "Vamos a hacer el diagnóstico. La pantalla está dañada: ¿el teléfono enciende y el táctil funciona normalmente?"
    if issue == "charging":
        return "Vamos a hacer el diagnóstico. Al conectar el cargador, ¿aparece alguna señal de carga o permanece sin cargar?"
    if issue == "battery":
        return "Vamos a hacer el diagnóstico. ¿La batería se descarga rápido, está hinchada o el teléfono se apaga solo?"
    if issue == "power":
        return "Vamos a hacer el diagnóstico. Al intentar encenderlo, ¿vibra, emite algún sonido o muestra el logotipo?"
    if issue == "liquid":
        return "Vamos a hacer el diagnóstico. ¿Cuándo tuvo contacto con líquido y el teléfono sigue encendido? Evita cargarlo hasta evaluarlo."
    return "Vamos a hacer el diagnóstico. ¿Qué le sucede al teléfono? Puedes indicar: pantalla, no enciende, no carga, batería, cámara u otro problema."


def _ready_for_ticket(text: str, issue: str | None) -> bool:
    """Ticket creation requires an identified problem plus an explicit action."""
    return bool(issue and _has_repair_or_quote_request(text))


def execute(
    message,
    company_id=None,
    customer_id=None,
    service_id=None,
    intent=None,
    customer=None,
    language=None,
    **kwargs
):
    text = _normalize(message)
    issue = _issue_type(text)

    # Never create a ticket merely because the user mentioned a broken phone or
    # asked for a diagnosis. First collect diagnostic information conversationally.
    if _is_diagnostic_request(text) or not _ready_for_ticket(text, issue):
        return {
            "success": False,
            "workflow": "mobile_repair",
            "diagnostic_pending": True,
            "response": _diagnostic_response(issue, language or "es"),
            "metadata": {
                "company_id": company_id,
                "customer_id": customer_id,
                "service_id": service_id,
                "intent": intent,
                "language": language or "es",
                "issue_type": issue,
            },
        }

    normalized_language = (language or "es").lower()
    if normalized_language.startswith("pt"):
        response = "Perfeito. Já temos as informações básicas do problema. Posso registrar a solicitação para avaliação e orçamento."
    elif normalized_language.startswith("en"):
        response = "Great. We have the basic problem details. I can register the request for evaluation and an estimate."
    else:
        response = "Perfecto. Ya tenemos la información básica del problema. Puedo registrar la solicitud para evaluación y presupuesto."

    return {
        "success": True,
        "workflow": "mobile_repair",
        "diagnostic_pending": False,
        "response": response,
        "metadata": {
            "company_id": company_id,
            "customer_id": customer_id,
            "service_id": service_id,
            "intent": intent,
            "language": language or "es",
            "issue_type": issue,
        },
    }
