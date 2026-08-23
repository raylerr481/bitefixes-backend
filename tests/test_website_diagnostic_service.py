from app.services.website_diagnostic_service import extract_urls


def test_extract_urls_from_message():
    assert extract_urls("mira https://bitefixes.com/ y dime que mejorar") == ["https://bitefixes.com/"]


def test_extract_multiple_urls_without_duplicates():
    assert extract_urls("https://a.example https://a.example https://b.example") == [
        "https://a.example",
        "https://b.example",
    ]
