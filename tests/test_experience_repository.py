from app.ai.experience_memory import Experience
from app.ai.experience_repository import SupabaseExperienceRepository


class Result:
    def __init__(self, data):
        self.data = data


class Query:
    def __init__(self):
        self.payload = None
        self.filters = []

    def upsert(self, payload, on_conflict=None):
        self.payload = payload
        return self

    def select(self, value):
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, value):
        return self

    def execute(self):
        return Result([self.payload] if self.payload else [{"case_id": "case-1"}])


class Client:
    def __init__(self):
        self.query = Query()

    def table(self, name):
        assert name == "bitey_experiences"
        return self.query


def test_save_maps_experience_without_llm_fields():
    client = Client()
    repo = SupabaseExperienceRepository(client)
    result = repo.save(Experience("case-1", "computer_repair", ["slow"], {}, "upgrade_ram", "improved", True, "case", 0.8))
    assert result["case_id"] == "case-1"
    assert result["success"] is True
    assert "password" not in result


def test_similar_queries_problem_only():
    client = Client()
    repo = SupabaseExperienceRepository(client)
    rows = repo.similar("computer_repair", 3)
    assert rows[0]["case_id"] == "case-1"
