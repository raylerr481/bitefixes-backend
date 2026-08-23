"""Safe, bounded website fetching for Bitey business diagnostics."""
from __future__ import annotations

import html
import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_MAX_BYTES = 1_000_000
_MAX_TEXT = 20_000
_TIMEOUT = 8


def extract_urls(text: str) -> list[str]:
    found: list[str] = []
    for raw in _URL_RE.findall(str(text or "")):
        url = raw.rstrip(".,);]}")
        if url not in found:
            found.append(url)
    return found


def _public_host(hostname: str) -> bool:
    if not hostname:
        return False
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, None)}
    except OSError:
        return False
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return False
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            return False
    return True


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        raise ValueError("Only public HTTP(S) URLs are supported")
    hostname = parsed.hostname
    if not hostname or not _public_host(hostname):
        raise ValueError("URL host is not a public address")
    return url


class _SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        absolute = urljoin(req.full_url, newurl)
        _validate_url(absolute)
        return super().redirect_request(req, fp, code, msg, headers, absolute)


def _visible_text(markup: str) -> str:
    cleaned = re.sub(r"<script\b[^>]*>.*?</script>", " ", markup, flags=re.I | re.S)
    cleaned = re.sub(r"<style\b[^>]*>.*?</style>", " ", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"<noscript\b[^>]*>.*?</noscript>", " ", cleaned, flags=re.I | re.S)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:_MAX_TEXT]


def _meta(markup: str, name: str) -> str:
    pattern = rf"<meta[^>]+(?:name|property)=[\"']{re.escape(name)}[\"'][^>]+content=[\"'](.*?)[\"']"
    match = re.search(pattern, markup, flags=re.I | re.S)
    return html.unescape(match.group(1)).strip()[:1000] if match else ""


def fetch_website_context(url: str) -> dict:
    target = _validate_url(url)
    request = Request(target, headers={"User-Agent": "BiteyWebsiteDiagnostic/1.0", "Accept": "text/html,application/xhtml+xml"})
    opener = build_opener(_SafeRedirectHandler)
    with opener.open(request, timeout=_TIMEOUT) as response:
        content_type = str(response.headers.get("Content-Type") or "").lower()
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            raise ValueError("URL does not expose an HTML document")
        body = response.read(_MAX_BYTES + 1)
        if len(body) > _MAX_BYTES:
            raise ValueError("Website response exceeds the diagnostic size limit")
        final_url = _validate_url(str(response.geturl() or target))

    markup = body.decode("utf-8", errors="ignore")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", markup, flags=re.I | re.S)
    title = html.unescape(re.sub(r"\s+", " ", title_match.group(1)).strip())[:500] if title_match else ""
    links = []
    for href in re.findall(r"<a[^>]+href=[\"']([^\"']+)[\"']", markup, flags=re.I):
        absolute = urljoin(final_url, href)
        if absolute.startswith(("http://", "https://")) and absolute not in links:
            links.append(absolute)
        if len(links) >= 30:
            break

    return {
        "url": target,
        "final_url": final_url,
        "title": title,
        "description": _meta(markup, "description"),
        "og_title": _meta(markup, "og:title"),
        "og_description": _meta(markup, "og:description"),
        "text": _visible_text(markup),
        "link_count": len(links),
        "sample_links": links[:20],
    }
