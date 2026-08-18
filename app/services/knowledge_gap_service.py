"""Bitey Knowledge Gap Service V1.

Identifies information that is missing or weak in a business/semantic context.
The result is a research input, not an instruction to trust external data.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List


DEFAULT_BUSINESS_FIELDS = (
    "industry",
    "business_model",
    "target_customer",
    "products_services",
    "sales_channels",
    "business_domains",
    "capabilities",
    "operational_needs",
)


def detect_gaps(context: Dict[str, Any], required_fields: Iterable[str] = DEFAULT_BUSINESS_FIELDS) -> List[Dict[str, Any]]:
    gaps = []
    for field in required_fields:
        value = context.get(field)
        missing = value is None or value == "" or value == [] or value == {}
        if missing:
            gaps.append({"field": field, "priority": "high"})
    return gaps


def build_research_questions(gaps: Iterable[Dict[str, Any]], company_name: str | None = None) -> List[str]:
    prefix = f"For {company_name}: " if company_name else ""
    templates = {
        "industry": "identify the company's primary industry and relevant sub-industries",
        "business_model": "identify the company's business model and revenue model",
        "target_customer": "identify the company's target customer segments",
        "products_services": "identify the company's products and services",
        "sales_channels": "identify the company's principal sales and communication channels",
        "business_domains": "identify the company's principal business domains and processes",
        "capabilities": "identify the company's relevant capabilities",
        "operational_needs": "identify likely operational needs relevant to the requested objective",
    }
    questions = []
    for gap in gaps:
        field = gap.get("field")
        if field in templates:
            questions.append(prefix + templates[field])
        elif field:
            questions.append(prefix + f"determine the relevant information for {field}")
    return questions
