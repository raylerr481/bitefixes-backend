"""Outbound connection security policy for Bitey connectors."""

from ipaddress import ip_address
from urllib.parse import urlparse


class ConnectionSecurityError(ValueError):
    """Raised when an outbound integration target is unsafe."""


def validate_endpoint_url(url: str, allowed_hosts=None) -> str:
    """Validate an HTTPS integration endpoint and reject private/local targets."""
    if not url or not isinstance(url, str):
        raise ConnectionSecurityError("endpoint_required")
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ConnectionSecurityError("https_endpoint_required")

    host = parsed.hostname.rstrip(".").lower()
    if allowed_hosts is not None:
        allowed = {str(h).rstrip(".").lower() for h in allowed_hosts}
        if host not in allowed:
            raise ConnectionSecurityError("host_not_allowed")

    try:
        ip = ip_address(host)
    except ValueError:
        ip = None

    if ip is not None and (
        ip.is_private or ip.is_loopback or ip.is_link_local
        or ip.is_reserved or ip.is_unspecified or ip.is_multicast
    ):
        raise ConnectionSecurityError("private_or_local_target_blocked")

    return url
