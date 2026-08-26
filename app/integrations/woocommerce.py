"""Safe, read-only WooCommerce connectivity helpers."""

import httpx

from app.config import settings


class WooCommerceConfigurationError(RuntimeError):
    pass


def _credentials() -> tuple[str, str, str]:
    url = settings.WOOCOMMERCE_URL
    key = settings.WOOCOMMERCE_CONSUMER_KEY
    secret = settings.WOOCOMMERCE_CONSUMER_SECRET
    if not url or not key or not secret:
        raise WooCommerceConfigurationError("WooCommerce credentials are not configured")
    return url.rstrip("/"), key, secret


def check_connection() -> dict:
    url, key, secret = _credentials()
    endpoint = f"{url}/wp-json/wc/v3/products"
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        response = client.get(endpoint, auth=(key, secret), params={"per_page": 1})
    if response.status_code != 200:
        return {"status": "error", "http_status": response.status_code, "endpoint": "/wp-json/wc/v3/products"}
    data = response.json()
    return {"status": "ok", "http_status": 200, "endpoint": "/wp-json/wc/v3/products", "products_returned": len(data)}
