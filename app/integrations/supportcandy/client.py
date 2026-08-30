"""SupportCandy REST client."""
from __future__ import annotations

import base64
import json
import os
from typing import Any
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


class SupportCandyConfigurationError(RuntimeError):
    pass


class SupportCandyClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("SUPPORTCANDY_URL", "https://bitefixes.com").rstrip("/") + "/"
        self.username = os.getenv("SUPPORTCANDY_USERNAME", "").strip()
        self.app_password = os.getenv("SUPPORTCANDY_APP_PASSWORD", "").strip()
        self.timeout = float(os.getenv("SUPPORTCANDY_TIMEOUT", "20"))
        if not self.username or not self.app_password:
            raise SupportCandyConfigurationError(
                "SUPPORTCANDY_USERNAME and SUPPORTCANDY_APP_PASSWORD are required"
            )

    def _request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = urljoin(self.base_url, path.lstrip("/"))
        if params:
            url += "?" + urlencode(params)
        token = base64.b64encode(f"{self.username}:{self.app_password}".encode()).decode()
        request = Request(url, headers={"Authorization": f"Basic {token}", "Accept": "application/json"}, method="GET")
        with urlopen(request, timeout=self.timeout) as response:
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
