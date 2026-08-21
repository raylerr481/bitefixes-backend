"""Company document ingestion and external-AI profiling.

The WordPress widget is only a transport/facade. This service extracts source
text, asks the external AI council to characterize the company, validates the
candidate structure, and persists the resulting company-scoped knowledge.
"""
from __future__ import annotations

import io
import json
import re
from hashlib import sha256
from pathlib import Path
from typing import Any

from app.ai.company_intelligence import (
    build_company_profile,
    persist_company_profile,
    record_ai_learning_event,
    record_company_knowledge,
)
from app.ai.runtime import build_ai_orchestrator

MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt", "csv", "json", "md"}


def _extension(filename: str) -> str:
    return Path(filename or "").suffix.lower().lstrip(".")


def _extract_docx(data: bytes) -> str:
    from docx import Document

    document = Document(io.BytesIO(data))
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


def extract_text(filename: str, data: bytes) -> str:
    ext = _extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("unsupported_attachment")
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("attachment_too_large")
    if ext == "pdf":
        text = _extract_pdf(data)
    elif ext == "docx":
        text = _extract_docx(data)
    elif ext == "doc":
        raise ValueError("legacy_doc_not_supported")
    else:
        text = data.decode("utf-8-sig", errors="replace")
    text = text.strip()
    if not text:
        raise ValueError("empty_document")
    return text


def _parse_json_answer(answer: Any) -> dict[str, Any]:
    if isinstance(answer, dict):
        return answer
    text = str(answer or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            return {}
        try:
            value = json.loads(match.group(0))
            return value if isinstance(value, dict) else {}
        except json.JSONDecodeError:
            return {}


def _analysis_prompt(text: str, filename: str, company_id: int) -> str:
    return f"""You are an external business intelligence analyst training Bitey.
Bitey is not the cognitive authority yet. Do not invent facts and do not execute
business actions. Analyze the supplied company source and return ONLY valid JSON.

Company id: {company_id}
Source file: {filename}

Required JSON shape:
{{
  "company_name": null,
  "description": null,
  "industry": null,
  "services": [],
  "capabilities": [],
  "technologies": [],
  "customer_types": [],
  "business_rules": [],
  "facts": [],
  "knowledge_records": [
    {{"knowledge_type":"fact|service|policy|faq|process", "title":"", "content":"", "service_key":null, "confidence":0.0}}
  ],
  "uncertainties": []
}}

Only assert information supported by the source. Keep services specific enough
that future customer questions can be mapped to them. The knowledge records are
training candidates, not autonomous instructions.

SOURCE TEXT:
{text[:120000]}
"""


async def import_company_document(
    *,
    company_id: int,
    filename: str,
    data: bytes,
    source_type: str = "document",
    source_uri: str = "",
    channel: str = "website",
    conversation_id: str = "",
) -> dict[str, Any]:
    text = extract_text(filename, data)
    digest = sha256(data).hexdigest()
    orchestrator = build_ai_orchestrator()
    result = await orchestrator.ask_council(
        _analysis_prompt(text, filename, company_id),
        capability="extraction",
        context={
            "company_id": company_id,
            "channel": channel,
            "conversation_id": conversation_id,
            "source_type": source_type,
        },
        max_providers=3,
    )

    candidates = []
    for candidate in result.get("candidates", []):
        analysis = _parse_json_answer(candidate.get("answer"))
        if analysis:
            analysis["provider"] = candidate.get("provider")
            candidates.append(analysis)

    if not candidates:
        record_ai_learning_event(
            company_id=company_id,
            event={
                "event_type": "company_document_analysis_failed",
                "input_context": {"filename": filename, "source_type": source_type},
                "provider_outputs": result.get("candidates", []),
                "decision": {"status": "rejected", "reason": "no_structured_candidate"},
                "outcome": {"stored": False},
            },
        )
        raise RuntimeError("no_structured_ai_candidate")

    source = {
        "source_type": "pdf" if _extension(filename) == "pdf" else source_type,
        "name": filename,
        "uri": source_uri,
        "content_hash": digest,
        "metadata": {"channel": channel, "conversation_id": conversation_id, "bytes": len(data)},
    }
    profile = build_company_profile(company_id=company_id, analyses=candidates, sources=[source])
    persisted = persist_company_profile(profile)

    knowledge_records = []
    for analysis in candidates:
        provider = str(analysis.get("provider") or result.get("provider") or "external-ai")
        for record in analysis.get("knowledge_records", []):
            if not isinstance(record, dict) or not str(record.get("content") or "").strip():
                continue
            record = dict(record)
            record["provider"] = provider
            record["source_type"] = source["source_type"]
            record["source_uri"] = source_uri
            knowledge_records.append(record)
    knowledge_count = record_company_knowledge(
        company_id=company_id,
        records=knowledge_records,
        provider=str(result.get("provider") or "external-ai-council"),
    )

    record_ai_learning_event(
        company_id=company_id,
        event={
            "event_type": "company_document_profiled",
            "input_context": {"filename": filename, "source_type": source_type, "digest": digest},
            "provider_outputs": result.get("candidates", []),
            "decision": {"status": "accepted", "providers": profile.get("analyst_providers", [])},
            "outcome": {"profile_stored": bool(persisted), "knowledge_records": knowledge_count},
        },
    )

    return {
        "response": "Documento analizado. El perfil de la empresa y su conocimiento candidato fueron registrados para mejorar las respuestas futuras.",
        "company_profile": persisted or profile,
        "learning_candidate": {
            "status": "registered",
            "providers": profile.get("analyst_providers", []),
            "knowledge_records": knowledge_count,
        },
        "council": {
            "selected_provider": result.get("provider"),
            "providers_consulted": [c.get("provider") for c in result.get("candidates", [])],
            "council_used": result.get("council_used", False),
        },
    }
