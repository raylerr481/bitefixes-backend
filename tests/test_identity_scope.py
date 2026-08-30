from app.cognitive.identity_scope import IdentityScope


def test_same_company_channel_conversation_is_stable():
    a = IdentityScope(1, "website", "conv-1", user_id="u-1")
    b = IdentityScope(1, "website", "conv-1", user_id="u-1")
    assert a.key() == b.key()


def test_companies_are_isolated():
    a = IdentityScope(1, "website", "conv-1", user_id="u-1")
    b = IdentityScope(2, "website", "conv-1", user_id="u-1")
    assert a.key() != b.key()


def test_channels_are_isolated():
    a = IdentityScope(1, "website", "conv-1", user_id="u-1")
    b = IdentityScope(1, "whatsapp", "conv-1", user_id="u-1")
    assert a.key() != b.key()


def test_external_message_id_has_priority_for_deduplication():
    a = IdentityScope(1, "whatsapp", "conv-1", user_id="u-1", external_message_id="wamid.123")
    b = IdentityScope(1, "whatsapp", "conv-1", user_id="u-1", external_message_id="wamid.123")
    assert a.message_key("texto A") == b.message_key("texto B")
