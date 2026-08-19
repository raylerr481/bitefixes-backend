"""Safe evaluation helpers for multi-model answers."""
from typing import Any


def evaluate_candidates(candidates: list[dict[str, Any]], *, core_confidence: float = 0.0) -> dict[str, Any]:
    """Evaluate model observations; never grant them business authority."""
    valid = [c for c in candidates if c.get("answer")]
    if not valid:
        return {"status":"no_candidates","confidence":0.0,"consensus":None,"learning_candidate":False}
    answers=[str(c["answer"]).strip() for c in valid]
    unique=list(dict.fromkeys(answers))
    agreement=1.0 if len(unique)==1 else len(valid)/(len(valid)+len(unique))
    score=round((agreement*0.7)+(min(max(core_confidence,0),1)*0.3),3)
    return {
        "status":"evaluated",
        "confidence":score,
        "consensus":unique[0] if len(unique)==1 else None,
        "candidate_count":len(valid),
        "learning_candidate": score >= 0.65,
    }
