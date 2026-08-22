"""Company AI Profile document ingestion endpoint."""
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app.services.company_document_service import ingest_company_document

router = APIRouter(prefix="/company-profile", tags=["company-profile"])

_ALLOWED = {"pdf", "docx", "txt", "csv", "json", "md"}
_MAX_BYTES = 10 * 1024 * 1024

@router.post("/import")
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
        result = ingest_company_document(company_id=company_id, company_name=company_name.strip(), filename=filename, content=content, content_type=file.content_type or "application/octet-stream")
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
