"""Small deterministic multilingual lexicon used before external AI.

This is intentionally additive: database semantic knowledge remains the
source of truth. The lexicon handles common spelling mistakes, variants and
cross-language terms so Bitey can route simple requests without an LLM.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List


LEXICON: Dict[str, List[str]] = {
    "mobile_repair": [
        "celular", "celulares", "telefone", "telefones", "mobile", "smartphone",
        "phone", "cellphone", "iphone", "samsung", "xiaomi", "motorola",
    ],
    "screen_repair": [
        "pantalla", "pantalla rota", "pantalla quebrada", "display", "tela",
        "tela quebrada", "tela quebrada", "screen", "screen broken", "display broken",
        "aptanla", "pantalal", "pantalla rota", "tela trincada",
    ],
    "battery_repair": [
        "bateria", "battery", "batería", "bateria inchada", "battery replacement",
    ],
    "computer_repair": [
        "computadora", "computador", "ordenador", "pc", "notebook", "laptop",
        "computer", "desktop", "computadora rota", "pc no funciona",
    ],
    "network_configuration": [
        "red", "redes", "wifi", "wi-fi", "internet", "roteador", "router",
        "network", "networking", "rede", "rede wifi",
    ],
    "cctv_installation": [
        "camara", "camaras", "cámara", "cámaras", "cctv", "camera", "cameras",
        "videovigilancia", "vigilancia", "seguridad",
    ],
    "business_ai": [
        "ia para empresa", "ia empresarial", "inteligencia artificial", "ai",
        "business ai", "automacao", "automação", "automatizacion", "automatización",
        "agente ia", "ai agent", "crm", "automatizar empresa",
    ],
}


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


NORMALIZED_LEXICON = {
    key: [normalize(term) for term in terms]
    for key, terms in LEXICON.items()
}


def candidates(text: str) -> List[str]:
    """Return intents/capabilities whose lexical variants occur in text."""
    value = normalize(text)
    found: List[str] = []
    for concept, terms in NORMALIZED_LEXICON.items():
        if any(term and term in value for term in terms):
            found.append(concept)
    return found
