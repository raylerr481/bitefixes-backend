"""Company AI Profile ingestion and enterprise assessment endpoints."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.security.channel_auth import require_channel_key
from app.services.company_document_service import ingest_company_document
from app.services.enterprise_configuration import assess_enterprise_profile, build_configuration_manifest

router = APIRouter(prefix="/company-profile", tags=["company-profile"])
_ALLOWED = {"pdf", "docx", "txt", "csv", "json", "md"}
_MAX_BYTES = 10 * 1024 * 1024


class EnterpriseAssessmentRequest(BaseModel):
    profile: dict = Field(default_factory=dict)


class EnterpriseManifestRequest(BaseModel):
    profile: dict = Field(default_factory=dict)
    version: str = "1.0"


@router.post("/import", dependencies=[Depends(require_channel_key)])
async def import_company_document(
    company_id: int = Form(...),
    company_name: str = Form(""),
    source: str = Form("wordpress"),
    channel: str = Form("website"),
    file: UploadFile = File(...),
):
    filename = file.filename or "document"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in _ALLOWED:
        raise HTTPException(status_code=400, detail="Unsupported document type. Use PDF, DOCX, TXT, CSV, JSON or MD.")
    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Document exceeds the 10 MB limit.")
    try:
        result = ingest_company_document(
            company_id=company_id,
            company_name=company_name.strip(),
            filename=filename,
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print("[COMPANY DOCUMENT INGESTION ERROR]", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Company document could not be ingested.") from exc
    result["source"] = source
    result["channel"] = channel
    return result


@router.post("/assessment", dependencies=[Depends(require_channel_key)])
def enterprise_assessment(body: EnterpriseAssessmentRequest):
    """Assess what Bitey still needs before adapting to a company."""
    return assess_enterprise_profile(body.profile)


@router.post("/configuration-preview", dependencies=[Depends(require_channel_key)])
def enterprise_configuration_preview(body: EnterpriseManifestRequest):
    """Compile a reviewed, non-secret tenant configuration manifest."""
    try:
        manifest = build_configuration_manifest(body.profile, version=body.version)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "success", "manifest": manifest}
