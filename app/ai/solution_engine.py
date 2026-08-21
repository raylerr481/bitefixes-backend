"""Generate conservative solution candidates from verified diagnostic state."""
from typing import Any, Dict, List


class SolutionEngine:
    """Produces ranked candidates; it does not create tickets or mutate knowledge."""

    def propose(self, problem: str | None, hypotheses: List[Dict[str, Any]], evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not problem or not hypotheses:
            return []
        top = hypotheses[0]
        name = str(top.get("name", "unknown"))
        candidates = {
            "screen_damage": [
                "Verificar encendido y funcionamiento del táctil.",
                "Inspeccionar el conjunto de pantalla antes de cotizar reemplazo.",
            ],
            "charging_failure": [
                "Probar otro cable y fuente compatibles.",
                "Inspeccionar puerto de carga y batería antes de sustituir componentes.",
            ],
            "low_storage": [
                "Liberar espacio y revisar procesos de inicio.",
                "Comprobar salud del almacenamiento antes de recomendar reemplazo.",
            ],
        }
        return [{"hypothesis": name, "action": action, "requires_verification": True} for action in candidates.get(name, ["Realizar una prueba diagnóstica adicional antes de intervenir."])]
