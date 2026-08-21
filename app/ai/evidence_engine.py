"""Evidence and hypothesis utilities for Bitey diagnostics."""
from typing import Any, Dict, List


class EvidenceEngine:
    """Ranks hypotheses from explicit observations without calling external AI."""

    def score(self, hypotheses: List[Dict[str, Any]], evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        scored = []
        for hypothesis in hypotheses:
            item = dict(hypothesis)
            name = str(item.get("name", "")).lower()
            support = 0
            contradiction = 0
            for observation in evidence:
                text = str(observation.get("observation", "")).lower()
                target = str(observation.get("supports", "")).lower()
                if target and target == name:
                    support += 1
                if target and target != name and name and name in text:
                    contradiction += 1
            item["evidence_score"] = max(0, support - contradiction)
            scored.append(item)
        return sorted(scored, key=lambda x: (x.get("evidence_score", 0), x.get("confidence", 0)), reverse=True)

    @staticmethod
    def next_question(unknowns: List[str]) -> str | None:
        if not unknowns:
            return None
        questions = {
            "screen_power": "¿El teléfono enciende normalmente?",
            "touch": "¿El táctil funciona normalmente?",
            "charging": "¿El teléfono muestra que está cargando?",
            "battery": "¿La batería se descarga rápidamente o se apaga?",
            "storage": "¿Cuánto espacio libre queda en el dispositivo?",
            "ram": "¿Cuánta memoria RAM tiene el equipo?",
        }
        return questions.get(unknowns[0], f"¿Puedes aportar información sobre {unknowns[0]}?")
