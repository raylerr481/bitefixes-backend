import pytest

from app.services.connection_security import ConnectionSecurityError, validate_endpoint_url


def test_requires_https():
    with pytest.raises(ConnectionSecurityError):
        validate_endpoint_url("http://example.com/api")


def test_blocks_private_ip():
    with pytest.raises(ConnectionSecurityError):
        validate_endpoint_url("https://127.0.0.1/api")


def test_blocks_disallowed_host():
    with pytest.raises(ConnectionSecurityError):
        validate_endpoint_url("https://api.example.com", allowed_hosts=["trusted.example.com"])


def test_accepts_allowed_public_https_host():
    assert validate_endpoint_url("https://api.example.com", allowed_hosts=["api.example.com"]) == "https://api.example.com"
