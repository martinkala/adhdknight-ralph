"""HTTP client for the Food diary API (`/api/v1/food/*`), same conventions as core/api_client.py:
success returns the parsed JSON, failure returns {"error": "server_unavailable" | "unauthorized" | "server_error"}.
Views call it through `call(request, ...)`, which refreshes an expired access token (core.api_client.call_with_refresh)."""
import httpx
from django.conf import settings

from core.api_client import call_with_refresh

_TIMEOUT = 5.0
_PREFIX = "/api/v1/food"


def _url(path: str) -> str:
    return f"{settings.SERVER_URL}{_PREFIX}{path}"


def request(token: str, method: str, path: str, json: dict | None = None, params: dict | None = None) -> dict:
    try:
        r = httpx.request(
            method,
            _url(path),
            json=json,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=_TIMEOUT,
        )
        if r.status_code in (200, 201):
            return r.json()
        if r.status_code == 204:
            return {}
        if r.status_code == 401:
            return {"error": "unauthorized"}
        return {"error": "server_error", "status_code": r.status_code}
    except (httpx.ConnectError, httpx.TimeoutException):
        return {"error": "server_unavailable"}


def get(token: str, path: str, params: dict | None = None) -> dict:
    return request(token, "GET", path, params=params)


def post(token: str, path: str, json: dict | None = None) -> dict:
    return request(token, "POST", path, json=json)


def call(django_request, method: str, path: str, json: dict | None = None, params: dict | None = None) -> dict:
    return call_with_refresh(django_request, request, method, path, json=json, params=params)
