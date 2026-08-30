"""SupportCandy REST client."""
from __future__ import annotations

import base64
import json
from typing import Any
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from app.config import settings


class SupportCandyConfigurationError(RuntimeError):
    pass


class SupportCandyClient:
    def __init__(self) -> None:
        self.base_url = (settings.SUPPORTCANDY_URL or "").rstrip("/") + "/"
        self.username = settings.SUPPORTCANDY_USERNAME or ""
        self.app_password = settings.SUPPORTCANDY_APP_PASSWORD or ""
        if not self.base_url or not self.username or not self.app_password:
            raise SupportCandyConfigurationError(
                "SUPPORTCANDY_URL, SUPPORTCANDY_USERNAME and SUPPORTCANDY_APP_PASSWORD are required"
            )

    def _request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = urljoin(self.base_url, path.lstrip("/"))
        if params:
            url += "?" + urlencode(params)
        token = base64.b64encode(f"{self.username}:{self.app_password}".encode()).decode()
        request = Request(url, headers={"Authorization": f"Basic {token}", "Accept": "application/json"}, method="GET")
        with urlopen(request, timeout=settings.SUPPORTCANDY_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _items(payload: Any, key: str) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            value = payload.get("data", payload.get(key, []))
            return value if isinstance(value, list) else []
        return []

    def list_tickets(self, page: int = 1, per_page: int = 100) -> list[dict[str, Any]]:
        payload = self._request("/wp-json/supportcandy/v2/tickets", {"page": page, "per_page": per_page, "filter": "all", "orderby": "date_updated", "order": "ASC"})
        return self._items(payload, "tickets")

    def get_threads(self, ticket_id: int, page: int = 1, per_page: int = 100) -> list[dict[str, Any]]:
        payload = self._request(f"/wp-json/supportcandy/v2/tickets/{ticket_id}/threads", {"page": page, "per_page": per_page, "order": "ASC"})
        return self._items(payload, "threads")
