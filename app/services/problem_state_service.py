"""General semantic conversation/problem state for Bitey.

Important: object mentions are not symptoms. A service request establishes a goal;
only explicit symptom evidence may establish an active problem. Short replies are
resolved against the active conversation state and any pending question.
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
    r"\b(redmi\s+[a-z0-9][a-z0-9 ._-]{0,24})\b", r"\b(xiaomi\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(iphone\s+[a-z0-9][a-z0-9 ._-]{0,24})\b", r"\b(samsung\s+(?:galaxy\s+)?[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(galaxy\s+[a-z0-9][a-z0-9 ._-]{0,24})\b", r"\b(moto(?:rola)?\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(thinkpad\s+[a-z0-9][a-z0-9 ._-]{0,24})\b", r"\b(dell\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
    r"\b(hp\s+[a-z0-9][a-z0-9 ._-]{0,24})\b", r"\b(lenovo\s+[a-z0-9][a-z0-9 ._-]{0,24})\b", r"\b(acer\s+[a-z0-9][a-z0-9 ._-]{0,24})\b",
)
_OBJECTS = {
    "phone": ("telefono", "teléfono", "movil", "móvil", "celular", "smartphone", "android", "iphone"),
    "computer": ("notebook", "laptop", "computadora", "ordenador", "pc", "windows", "macbook", "linux"),
    "tablet": ("tablet", "ipad"), "network": ("router", "switch", "wifi", "wi-fi", "red", "access point", "punto de acceso"),
    "server": ("servidor", "server", "windows server", "proxmox"), "printer": ("impresora", "printer"),
    "camera": ("camara", "cámara", "cctv", "dvr", "nvr"), "business_system": ("crm", "saas", "wordpress", "woocommerce", "empresa", "negocio"),
}

_REQUEST_PATTERNS = re.compile(r"\b(?:quiero|quisiera|deseo|necesito|me gustaria|me gustaría|busco|solicito|pretendo)\b.*\b(?:instalar|crear|configurar|comprar|contratar|montar|hacer|adquirir|implementar|poner|arreglar|reparar|cambiar)\b", re.I)
_REQUEST_PATTERNS_2 = re.compile(r"\b(?:instalar|crear|configurar|comprar|contratar|montar|adquirir|implementar|reparar|arreglar|cambiar)\b", re.I)
_SYMPTOM_PATTERNS = re.compile(r"\b(?:no funciona|no muestra|no se ve|se corta|falla|fallando|falló|fallo|problema|problemas|aver[ií]a|averiado|roto|dañado|lento|lenta|no enciende|no inicia|no conecta|no carga|quebrada|quebrado)\b", re.I)

_PENDING_FIELD_PATTERNS = (
    ("model", re.compile(r"\b(?:modelo|model)\b", re.I)),
    ("os_version", re.compile(r"\b(?:versi[oó]n|version)\b.*\b(?:windows|android|ios|sistema)\b|\b(?:windows|android|ios)\b.*\b(?:versi[oó]n|version)\b", re.I)),
    ("symptom", re.compile(r"\b(?:qué|que)\b.*\b(?:ocurre|pasa|problema|s[ií]ntoma)\b|\b(?:describe|describa)\b.*\b(?:problema|ocurre|pasa)\b", re.I)),
    ("location", re.compile(r"\b(?:d[oó]nde|donde|ubicaci[oó]n|ubicacion)\b", re.I)),
)

def _contains(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text.lower() for term in terms)

def _extract_model(text: str) -> str | None:
    for pattern in _MODEL_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            candidate = re.sub(r"\s+", " ", str(matches[-1]).strip(" .,_-\t\n"))
            candidate = re.split(r"\b(?:y|pero|solo|porque|que|con|esta|está|tiene|tengo|deseo|quiero)\b", candidate, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            if 2 <= len(candidate) <= 40: return candidate
    return None

def _extract_location(texts: list[str]) -> str | None:
    patterns = (r"\b(?:en|desde|estoy en|ubicado en|ubicada en)\s+([a-záéíóúñü][a-záéíóúñü0-9 .,'-]{2,80})", r"\b(esteio(?:\s+centro)?(?:\s*,?\s*porto\s+alegre)?(?:\s*,?\s*rio\s+grande\s+do\s+sul)?)\b")
    for text in reversed(texts):
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                candidate = (match.group(1) if match.lastindex else match.group(0)).strip(" .,_-\t\n")
                if 3 <= len(candidate) <= 90: return re.sub(r"\s+", " ", candidate)
    return None

def _extract_objects(text: str) -> list[str]:
    return [name for name, terms in _OBJECTS.items() if _contains(text, terms)]

def _pending_question(history: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Infer what Bitey most recently asked for, without hard-coding device names."""
    for row in reversed(history[-6:]):
        sender = str(row.get("sender_type") or row.get("role") or "").lower()
        if sender not in {"assistant", "agent", "bot"}: continue
        text = str(row.get("message_content") or row.get("content") or "").strip()
        if not text: continue
        for field, pattern in _PENDING_FIELD_PATTERNS:
            if pattern.search(text):
                return {"field": field, "question": text}
        if "?" in text and re.search(r"\b(?:podr[ií]as|puedes|puede|indica|indique|dime|decime|cu[aá]l|qu[eé])\b", text, re.I):
            return {"field": "unspecified", "question": text}
    return None

def build_problem_state(history: list[dict[str, Any]], current_message: str) -> dict[str, Any]:
    recent = history[-16:]
    user_rows = [r for r in recent if str(r.get("sender_type") or r.get("role") or "").lower() in {"customer", "user"}]
    user_texts = [str(r.get("message_content") or r.get("content") or "").strip() for r in user_rows if str(r.get("message_content") or r.get("content") or "").strip()]
    current = str(current_message or "").strip()
    prior_user = " ".join(user_texts)
    current_lower = current.lower()
    all_user = " ".join(user_texts + [current]).lower()

    request_present = bool(_REQUEST_PATTERNS.search(all_user) or _REQUEST_PATTERNS_2.search(current))
    explicit_symptom = bool(_SYMPTOM_PATTERNS.search(current))
    current_signal_scores = {group: sum(1 for term in terms if term in current_lower) for group, terms in _SIGNAL_GROUPS.items()}
    current_signal_scores = {g: s for g, s in current_signal_scores.items() if s}
    prior_signal_scores = {group: sum(1 for term in terms if term in prior_user.lower()) for group, terms in _SIGNAL_GROUPS.items()}
    prior_signal_scores = {g: s for g, s in prior_signal_scores.items() if s}
    prior_signals = list(prior_signal_scores)
    current_signals = list(current_signal_scores)
    objects = _extract_objects(all_user)
    current_objects = _extract_objects(current)
    model = _extract_model(all_user)
    location = _extract_location(user_texts + [current])
    pending = _pending_question(recent)

    detail_only = bool(user_texts and not explicit_symptom and not current_signals and (current_objects or model or location or pending))

    # A short reply to a pending question is contextual evidence, not a new problem.
    pending_answer = bool(pending and not explicit_symptom and not current_signals)
    active_category = None
    if explicit_symptom and current_signals:
        active_category = max(current_signals, key=lambda g: current_signal_scores.get(g, 0))
    elif current_signals:
        active_category = max(current_signals, key=lambda g: current_signal_scores.get(g, 0))
    elif prior_signals and (detail_only or pending_answer or not current.strip()):
        active_category = max(prior_signals, key=lambda g: prior_signal_scores.get(g, 0))

    labels = {"security":"posible problema de seguridad","performance":"problema de rendimiento","startup":"problema de inicio/arranque","connectivity":"problema de conectividad","power":"problema de energía/batería","display":"problema de pantalla/interfaz","audio":"problema de audio","camera":"problema de cámara/vídeo","printing":"problema de impresión","software":"problema de software","accounts":"problema de acceso/cuenta","data":"problema de datos/recuperación","physical_damage":"posible daño físico","business_ai":"problema o necesidad de sistema empresarial/IA"}
    active_problem = labels.get(active_category) if active_category else None
    active_object = current_objects[0] if current_objects else (objects[0] if objects else None)

    hypotheses = []
    if active_category:
        score = current_signal_scores.get(active_category) or prior_signal_scores.get(active_category, 1)
        hypotheses.append({"category": active_category, "confidence": min(0.55 + 0.10 * score, 0.95), "basis": "current_evidence" if current_signals else "conversation_context"})
    customer_goal = None
    if re.search(r"\b(quiero hacerlo yo|hacerlo yo mismo|por mi cuenta|yo mismo|autoservicio|paso a paso)\b", all_user, re.I): customer_goal="SELF_SERVICE"
    elif re.search(r"\b(remoto|asistencia remota|soporte remoto)\b", all_user, re.I): customer_goal="REMOTE_ASSISTANCE"
    elif re.search(r"\b(taller|llevarlo|llevar el equipo|presencial)\b", all_user, re.I): customer_goal="WORKSHOP"
    elif re.search(r"\b(cuanto cuesta|cuánto cuesta|precio|presupuesto|cotizacion|cotización)\b", all_user, re.I): customer_goal="QUOTE"

    # A genuinely different explicit symptom category creates a new problem.
    new_problem = bool(active_category and prior_signals and current_signals and set(current_signals).isdisjoint(set(prior_signals)))
    if new_problem:
        state = "NEW_PROBLEM"
        active_goal = "SOLVE_PROBLEM"
    elif request_present and not active_problem:
        state = "GOAL_REQUEST"
        active_goal = "REQUEST_SERVICE"
    elif detail_only or pending_answer:
        state = "ENTITY_UPDATE" if pending and pending.get("field") == "model" else "CONTINUATION"
        active_goal = "SOLVE_PROBLEM" if active_problem else "REQUEST_SERVICE"
    elif active_category:
        state = "PROBLEM_UPDATE"
        active_goal = "SOLVE_PROBLEM"
    else:
        state = "CONTINUATION" if user_texts else "NEW_TURN"
        active_goal = "REQUEST_SERVICE" if request_present else None

    confidence = 0.82 if active_goal == "REQUEST_SERVICE" else (0.72 if active_problem else 0.50)
    facts=[]
    if active_object: facts.append({"type":"object","value":active_object})
    if model: facts.append({"type":"model","value":model})
    if active_problem: facts.append({"type":"problem","value":active_problem})
    if location: facts.append({"type":"location","value":location})
    if customer_goal: facts.append({"type":"customer_goal","value":customer_goal})
    if active_goal: facts.append({"type":"active_goal","value":active_goal})
    return {
        "state":state, "active_problem":active_problem, "active_category":active_category,
        "active_object":active_object, "active_model":model, "active_location":location,
        "active_goal":active_goal, "pending_question":pending, "pending_answer":pending_answer,
        "symptoms":current_signals, "hypotheses":hypotheses, "customer_goal":customer_goal,
        "confidence":round(confidence,3), "is_follow_up":bool(user_texts), "entity_only":detail_only,
        "confirmed_facts":facts, "signal_scores":current_signal_scores or prior_signal_scores,
        "problem_fingerprint":"|".join(x for x in (active_category or "",active_object or "") if x),
        "recent_turns":recent,
    }
