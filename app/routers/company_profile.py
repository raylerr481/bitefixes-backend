"""Company profile ingestion gateway for Bitey channels."""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.company_profile_import import ALLOWED_EXTENSIONS, MAX_DOCUMENT_BYTES, import_company_document

router = APIRouter(prefix="/company-profile", tags=["company-profile"])


@router.post("/import")
async def import_profile(
    company_id: int = Form(...),
    channel: str = Form("website"),
    conversation_id: str = Form(""),
    source_type: str = Form("document"),
    source_uri: str = Form(""),
    file: UploadFile = File(...),
):
    """Analyze a company document with the external AI council and persist it.

    The endpoint intentionally gives the uploaded content to the cognitive
    council but does not give any external provider direct database authority.
    Persistence is performed by BiteFixes Backend after structured validation.
    """
    filename = file.filename or "document"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="unsupported_attachment")

    data = await file.read()
    if len(data) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="attachment_too_large")

    try:
        return await import_company_document(
            company_id=company_id,
            filename=filename,
            data=data,
            source_type=source_type,
            source_uri=source_uri,
            channel=channel,
            conversation_id=conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
