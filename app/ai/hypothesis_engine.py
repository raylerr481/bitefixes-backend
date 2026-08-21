"""Deterministic hypothesis management for Bitey's investigative loop."""
from typing import Dict, List


class HypothesisEngine:
    def rank(self, hypotheses: List[Dict], evidence: List[Dict]) -> List[Dict]:
        ranked = []
        for hypothesis in hypotheses:
            item = dict(hypothesis)
            name = str(item.get("name", ""))
            score = float(item.get("confidence", 0.0))
            for ev in evidence:
                supports = str(ev.get("supports", ""))
                if supports == name:
                    score += 0.15
                elif ev.get("contradicts") == name:
                    score -= 0.20
            item["confidence"] = max(0.0, min(1.0, score))
            ranked.append(item)
        return sorted(ranked, key=lambda x: x["confidence"], reverse=True)

    def record_result(self, evidence: List[Dict], hypothesis: str, success: bool, observation: str) -> List[Dict]:
        evidence.append({
            "source": "verification",
            "observation": observation,
            "supports": hypothesis if success else None,
            "contradicts": None if success else hypothesis,
            "result": "success" if success else "failure",
        })
        return evidence
