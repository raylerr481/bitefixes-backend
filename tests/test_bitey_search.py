from app.ai.bitey_search import BLOCKED_PROVIDERS, _assert_allowed


def test_blocklist_never_allows_brave_or_major_search_apis():
    for provider in ("brave", "bing", "google", "braveapi"):
        assert provider in BLOCKED_PROVIDERS


def test_tavily_is_not_blocked():
    _assert_allowed("tavily")


def test_bitey_search_service_is_the_primary_name():
    assert "brave" not in BLOCKED_PROVIDERS
