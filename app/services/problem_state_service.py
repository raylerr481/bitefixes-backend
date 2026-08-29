"""General semantic conversation/problem state for Bitey.

This module is intentionally domain-general. It separates stable problem state
from new entities supplied by the customer, so a model name, location, symptom
or other fact cannot accidentally replace the active problem.
"""
from __future__ import annotations

import re
from typing import Any


_SIGNAL_GROUPS: dict[str, tuple[str, ...]] = {
    "security": ("virus", "malware", "infectado", "infeccion", "infección", "hackeado", "phishing", "ransomware", "espia", "espía", "publicidad invasiva", "anuncios solos"),
    "performance": ("lento", "lenta", "lentitud", "se congela", "congelado", "bloquea", "bloqueado", "rendimiento", "slow", "freezes", "lag"),
    "startup": ("no enciende", "no inicia", "no arranca", "no prende", "pantalla negra", "boot", "arranque", "startup"),
    "connectivity": ("wifi", "wi-fi", "internet", "red", "conexion", "conexión", "desconecta", "sin señal", "bluetooth", "ethernet"),
    "power": ("bateria", "batería", "no carga", "carga lento", "se apaga", "se descarga", "calienta", "sobrecalienta"),
    "display": ("pantalla", "display", "lcd", "touch", "táctil", "tactil", "brillo", "no muestra"),
    "audio": ("audio", "sonido", "altavoz", "microfono", "micrófono", "auricular"),
    "camera": ("camara", "cámara", "cctv", "dvr", "nvr", "video", "vídeo"),
    "printing": ("impresora", "imprime", "impresión", "impresion", "printer", "toner", "tinta"),
    "software": ("windows", "android", "ios", "aplicacion", "aplicación", "programa", "error", "actualizacion", "actualización", "driver", "controlador"),
    "accounts": ("cuenta", "contraseña", "contrasena", "login", "acceso", "no puedo entrar", "bloqueado", "autenticacion", "autenticación"),
    "data": ("archivo", "archivos", "datos", "borrar", "perdí", "perdi", "recuperar", "backup", "copia de seguridad", "disco"),
    "physical_damage": ("roto", "rota", "quebrado", "quebrada", "dañado", "danado", "golpe", "agua", "mojado", "crack", "broken", "damaged"),
    "business_ai": ("crm", "saas", "automatizacion", "automatización", "inteligencia artificial", "ia", "marketing", "clientes", "ventas", "proceso"),
}

_MODEL_PATTERNS = (
    r"\b(redmi\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(xiaomi\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(iphone\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(samsung\s+(?:galaxy\s+)?[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(galaxy\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(moto(?:rola)?\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(thinkpad\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(dell\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(hp\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(lenovo\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(acer\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
)

_OBJECTS = {
    "phone": ("telefono", "teléfono", "movil", "móvil", "celular", "smartphone", "android", "iphone"),
    "computer": ("notebook", "laptop", "computadora", "ordenador", "pc", "windows", "macbook", "linux"),
    "tablet": ("tablet", "ipad"),
    "network": ("router", "switch", "wifi", "wi-fi", "red", "access point", "punto de acceso"),
    "server": ("servidor", "server", "windows server", "proxmox"),
    "printer": ("impresora", "printer"),
    "camera": ("camara", "cámara", "cctv", "dvr", "nvr"),
    "business_system": ("crm", "saas", "wordpress", "woocommerce", "empresa", "negocio"),
}


def _contains(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _extract_model(text: str) -> str | None:
    for pattern in _MODEL_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            candidate = re.sub(r"\s+", " ", str(matches[-1]).strip(" .,_-\t\n"))
            candidate = re.split(r"\b(?:y|pero|solo|porque|que|con|esta|está|tiene|tengo|deseo|quiero)\b", candidate, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            if 2 <= len(candidate) <= 40:
                return candidate
    return None


def _extract_location(texts: list[str]) -> str | None:
    patterns = (
        r"\b(?:en|desde|estoy en|ubicado en|ubicada en)\s+([a-záéíóúñü][a-záéíóúñü0-9 .,'-]{2,80})",
        r"\b(esteio(?:\s+centro)?(?:\s*,?\s*porto\s+alegre)?(?:\s*,?\s*rio\s+grande\s+do\s+sul)?)\b",
    )
    for text in reversed(texts):
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                candidate = (match.group(1) if match.lastindex else match.group(0)).strip(" .,_-\t\n")
                if 3 <= len(candidate) <= 90:
                    return re.sub(r"\s+", " ", candidate)
    return None


def _extract_objects(text: str) -> list[str]:
    found: list[str] = []
    for name, terms in _OBJECTS.items():
        if _contains(text, terms):
            found.append(name)
    return found


def build_problem_state(history: list[dict[str, Any]], current_message: str) -> dict[str, Any]:
    """Infer a stable, evolving state without treating every turn as a new problem."""
    recent = history[-16:]
    user_rows = [r for r in recent if str(r.get("sender_type") or "").lower() in {"customer", "user"}]
    user_texts = [str(r.get("message_content") or "").strip() for r in user_rows if str(r.get("message_content") or "").strip()]
    current = str(current_message or "").strip()
    all_user = " ".join(user_texts + [current]).lower()

    signals: list[str] = []
    signal_scores: dict[str, int] = {}
    for group, terms in _SIGNAL_GROUPS.items():
        score = sum(1 for term in terms if term in all_user)
        if score:
            signals.append(group)
            signal_scores[group] = score

    prior_user = " ".join(user_texts[:-1]).lower() if user_texts else ""
    prior_signals = [g for g, terms in _SIGNAL_GROUPS.items() if any(term in prior_user for term in terms)]
    current_signals = [g for g, terms in _SIGNAL_GROUPS.items() if any(term in current.lower() for term in terms)]

    objects = _extract_objects(all_user)
    model = _extract_model(all_user)
    location = _extract_location(user_texts + [current])

    # A short turn containing mainly an entity is an update to the active case.
    words = current.split()
    entity_only = len(words) <= 8 and not current_signals and bool(model or objects or location)
    continuation = bool(user_texts) and (entity_only or not current_signals)

    active_category = None
    if current_signals:
        active_category = max(current_signals, key=lambda g: signal_scores.get(g, 0))
    elif prior_signals:
        # Preserve the prior problem when the new turn only adds context.
        active_category = prior_signals[-1]

    active_object = objects[0] if objects else None
    if active_object is None:
        active_object = "phone" if model and any(x in all_user for x in _OBJECTS["phone"]) else None

    # Human-readable problem summary. This is deliberately generic: it describes
    # the observed category rather than mapping one keyword to one service.
    problem_labels = {
        "security": "posible problema de seguridad",
        "performance": "problema de rendimiento",
        "startup": "problema de inicio/arranque",
        "connectivity": "problema de conectividad",
        "power": "problema de energía/batería",
        "display": "problema de pantalla/interfaz",
        "audio": "problema de audio",
        "camera": "problema de cámara/vídeo",
        "printing": "problema de impresión",
        "software": "problema de software",
        "accounts": "problema de acceso/cuenta",
        "data": "problema de datos/recuperación",
        "physical_damage": "posible daño físico",
        "business_ai": "problema o necesidad de sistema empresarial/IA",
    }
    active_problem = problem_labels.get(active_category) if active_category else None

    hypotheses: list[dict[str, Any]] = []
    if active_category:
        hypotheses.append({"category": active_category, "confidence": min(0.55 + 0.10 * signal_scores.get(active_category, 1), 0.95), "basis": "conversation_signals"})
    if active_category == "security":
        hypotheses.append({"category": "benign_or_non_malware_cause", "confidence": 0.30, "basis": "initial_claim_requires_verification"})
    if active_category == "performance":
        hypotheses.append({"category": "software_or_resource_cause", "confidence": 0.35, "basis": "requires_observation"})

    customer_goal = None
    if re.search(r"\b(quiero hacerlo yo|hacerlo yo mismo|por mi cuenta|yo mismo|autoservicio|paso a paso)\b", all_user, re.IGNORECASE):
        customer_goal = "SELF_SERVICE"
    elif re.search(r"\b(remoto|asistencia remota|soporte remoto)\b", all_user, re.IGNORECASE):
        customer_goal = "REMOTE_ASSISTANCE"
    elif re.search(r"\b(taller|llevarlo|llevar el equipo|presencial)\b", all_user, re.IGNORECASE):
        customer_goal = "WORKSHOP"
    elif re.search(r"\b(cuanto cuesta|cuánto cuesta|precio|presupuesto|cotizacion|cotización)\b", all_user, re.IGNORECASE):
        customer_goal = "QUOTE"

    state = "CONTINUATION" if continuation else ("NEW_PROBLEM" if not user_texts else "PROBLEM_UPDATE")
    if entity_only:
        state = "ENTITY_UPDATE"
    elif current_signals and prior_signals and set(current_signals).isdisjoint(set(prior_signals)):
        state = "NEW_PROBLEM"

    confidence = 0.50
    if active_problem:
        confidence = 0.72
        if len(signals) > 1:
            confidence = 0.78
    if entity_only and active_problem:
        confidence = min(confidence + 0.04, 0.92)

    facts = []
    if active_object:
        facts.append({"type": "object", "value": active_object})
    if model:
        facts.append({"type": "model", "value": model})
    if active_problem:
        facts.append({"type": "problem", "value": active_problem})
    if location:
        facts.append({"type": "location", "value": location})
    if customer_goal:
        facts.append({"type": "customer_goal", "value": customer_goal})

    return {
        "state": state,
        "active_problem": active_problem,
        "active_category": active_category,
        "active_object": active_object,
        "active_model": model,
        "active_location": location,
        "symptoms": signals,
        "hypotheses": hypotheses,
        "customer_goal": customer_goal,
        "confidence": round(confidence, 3),
        "is_follow_up": continuation,
        "entity_only": entity_only,
        "confirmed_facts": facts,
        "signal_scores": signal_scores,
        "problem_fingerprint": "|".join(sorted([active_category or "", active_object or "", model or ""]).strip().split("|")),
        "recent_turns": recent,
    }
