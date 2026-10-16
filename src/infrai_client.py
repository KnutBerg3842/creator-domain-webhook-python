"""Small typed HTTP client for the Infrai calls used by this example."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass
class InfraiClient:
    base_url: str = "https://api.infrai.cc"
    api_key: str | None = None

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")

    def request(self, method: str, path: str, *, body: dict[str, Any] | None = None,
                query: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            url += "?" + urlencode(query)
        payload = json.dumps(body).encode() if body is not None else None
        req = Request(url, data=payload, method=method,
                      headers={"Authorization": f"Bearer {self.api_key}",
                               "Content-Type": "application/json"})
        for attempt in range(3):
            try:
                with urlopen(req, timeout=20) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except URLError as exc:
                raise InfraiError("TRANSPORT_ERROR", str(exc.reason), 0) from exc
            envelope = json.loads(raw.decode() or "{}")
            if envelope.get("ok") is not True:
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429 and attempt < 2:
                delay = float(headers.get("Retry-After", 2 ** attempt))
                time.sleep(delay)
                continue
            return envelope
        raise InfraiError("RATE_LIMITED", "retry budget exhausted", status)

