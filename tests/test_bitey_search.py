from app.ai.bitey_search import BLOCKED_PROVIDERS, _assert_allowed


def test_blocklist_never_allows_brave_or_major_search_apis():
    for provider in ("brave", "bing", "google", "braveapi"):
        assert provider in BLOCKED_PROVIDERS


def test_tavily_is_not_blocked():
    _assert_allowed("tavily")


def test_blocklist_is_explicitly_brave_safe():
    assert "brave" in BLOCKED_PROVIDERS
    assert "braveapi" in BLOCKED_PROVIDERS
