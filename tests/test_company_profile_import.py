import pytest

from app.services import company_profile_import as importer


def test_extract_text_from_utf8_text():
    text = importer.extract_text("empresa.txt", "BiteFixes\nServicios: soporte, redes y CCTV".encode())
    assert "BiteFixes" in text
    assert "CCTV" in text


def test_rejects_oversized_document():
    with pytest.raises(ValueError, match="attachment_too_large"):
        importer.extract_text("empresa.txt", b"x" * (importer.MAX_DOCUMENT_BYTES + 1))


def test_rejects_unsupported_extension():
    with pytest.raises(ValueError, match="unsupported_attachment"):
        importer.extract_text("empresa.exe", b"hello")


@pytest.mark.asyncio
async def test_import_persists_structured_council_candidate(monkeypatch):
    class Council:
        async def ask_council(self, *args, **kwargs):
            return {
                "status": "ok",
                "provider": "groq",
                "council_used": True,
                "candidates": [
                    {
                        "provider": "groq",
                        "answer": '{"company_name":"BiteFixes","description":"IT services","industry":"technology","services":["CCTV"],"knowledge_records":[{"knowledge_type":"service","title":"CCTV","content":"Instalación de cámaras","service_key":"cctv","confidence":0.95}]}'
                    },
                    {
                        "provider": "deepseek-free",
                        "answer": '{"company_name":"BiteFixes","description":"IT services","industry":"technology","services":["CCTV"],"knowledge_records":[]}'
                    },
                ],
            }

    monkeypatch.setattr(importer, "build_ai_orchestrator", lambda: Council())
    monkeypatch.setattr(importer, "persist_company_profile", lambda profile: profile)
    monkeypatch.setattr(importer, "record_company_knowledge", lambda **kwargs: len(list(kwargs["records"])))
    monkeypatch.setattr(importer, "record_ai_learning_event", lambda **kwargs: {"ok": True})

    result = await importer.import_company_document(
        company_id=1,
        filename="empresa.txt",
        data=b"BiteFixes ofrece instalacion de CCTV.",
        source_type="document",
        channel="website",
    )

    assert result["company_profile"]["company_name"] == "BiteFixes"
    assert result["learning_candidate"]["status"] == "registered"
    assert result["learning_candidate"]["knowledge_records"] == 1
    assert result["council"]["providers_consulted"] == ["groq", "deepseek-free"]
