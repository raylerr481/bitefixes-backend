"""Persistence adapter for Bitey's episodic experience memory.

The repository is intentionally separate from ExperienceMemory so the reasoning
engine can be tested without a live database and production can use Supabase.
"""
from typing import Any, Dict, List

from app.ai.experience_memory import Experience


class SupabaseExperienceRepository:
    def __init__(self, client: Any, table: str = "bitey_experiences") -> None:
        self.client = client
        self.table = table

    def save(self, experience: Experience) -> Dict[str, Any]:
        payload = {
            "case_id": experience.case_id,
            "problem": experience.problem,
            "symptoms": experience.symptoms,
            "facts": experience.facts,
            "action": experience.action,
            "outcome": experience.outcome,
            "success": experience.success,
            "source": experience.source,
            "confidence": experience.confidence,
        }
        return self.client.table(self.table).upsert(payload, on_conflict="case_id").execute().data[0]

    def similar(self, problem: str, limit: int = 5) -> List[Dict[str, Any]]:
        return (
            self.client.table(self.table)
            .select("*")
            .eq("problem", problem)
            .order("confidence", desc=True)
            .limit(limit)
            .execute()
            .data
        )
