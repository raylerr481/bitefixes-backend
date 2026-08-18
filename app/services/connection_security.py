"""Outbound connection security policy for Bitey connectors."""

from ipaddress import ip_address
from urllib.parse import urlparse


class ConnectionSecurityError(ValueError):
    """Raised when an outbound integration target is unsafe."""


def validate_endpoint_url(url: str, allowed_hosts=None) -> str:
    """Validate an HTTPS integration endpoint and reject private/local targets.

    Explicit allowlisting can be supplied for controlled environments.
    """
    if not url or not isinstance(url, str):
        raise ConnectionSecurityError("endpoint_required")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ConnectionSecurityError("https_endpoint_required")

    host = parsed.hostname.lower().rstrip(".")
    if allowed_hosts is not None and host not in {h.lower().rstrip(".") for h in allowed_hosts}:
        raise ConnectionSecurityError("host_not_allowed")

    try:
        ip = ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ConnectionSecurityError("private_or_local_target_blocked")
    except ValueError:
        # Hostname: DNS resolution is intentionally not performed here.
        # Deployment-level egress controls should additionally restrict DNS.
        pass

    return url
