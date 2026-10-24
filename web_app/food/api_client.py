"""HTTP client for the Food diary API (`/api/v1/food/*`), same conventions as core/api_client.py:
success returns the parsed JSON, failure returns {"error": "server_unavailable" | "unauthorized" | "server_error"}
or, for a 4xx with a string API `detail` (e.g. "day_exists"), {"error": <detail>, "status_code": ...}.
Views call it through `call(request, ...)`, which refreshes an expired access token (core.api_client.call_with_refresh)."""
import httpx
from django.conf import settings

from core.api_client import call_with_refresh

_TIMEOUT = 5.0
_PREFIX = "/api/v1/food"


def _url(path: str) -> str:
    return f"{settings.SERVER_URL}{_PREFIX}{path}"


def request(
    token: str, method: str, path: str, json: dict | None = None, params: dict | None = None,
    timeout: float = _TIMEOUT,
) -> dict:
    try:
        r = httpx.request(
            method,
            _url(path),
            json=json,
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )
        if r.status_code in (200, 201):
            return r.json()
        if r.status_code == 204:
            return {}
        if r.status_code == 401:
            return {"error": "unauthorized"}
        if 400 <= r.status_code < 500:
            detail = r.json().get("detail") if r.headers.get("content-type", "").startswith("application/json") else None
            # FastAPI validation errors carry a list in `detail`.
            error = detail if isinstance(detail, str) else "invalid_input"
            return {"error": error, "status_code": r.status_code}
        return {"error": "server_error", "status_code": r.status_code}
    except (httpx.ConnectError, httpx.TimeoutException):
        return {"error": "server_unavailable"}


def get(token: str, path: str, params: dict | None = None) -> dict:
    return request(token, "GET", path, params=params)


def post(token: str, path: str, json: dict | None = None) -> dict:
    return request(token, "POST", path, json=json)


def call(
    django_request, method: str, path: str, json: dict | None = None, params: dict | None = None,
    timeout: float = _TIMEOUT,
) -> dict:
    return call_with_refresh(django_request, request, method, path, json=json, params=params, timeout=timeout)


def download(token: str, path: str, params: dict | None = None) -> dict:
    """GET of a file (export): {"content": bytes, "content_type": ..., "content_disposition": ...}
    or the same error dict as `request`."""
    try:
        r = httpx.get(_url(path), params=params, headers={"Authorization": f"Bearer {token}"}, timeout=_TIMEOUT)
    except (httpx.ConnectError, httpx.TimeoutException):
        return {"error": "server_unavailable"}
    if r.status_code == 200:
        return {
            "content": r.content,
            "content_type": r.headers.get("content-type", "application/octet-stream"),
            "content_disposition": r.headers.get("content-disposition", "attachment"),
        }
    if r.status_code == 401:
        return {"error": "unauthorized"}
    if 400 <= r.status_code < 500:
        detail = r.json().get("detail") if r.headers.get("content-type", "").startswith("application/json") else None
        return {"error": detail if isinstance(detail, str) else "invalid_input", "status_code": r.status_code}
    return {"error": "server_error", "status_code": r.status_code}


def call_download(django_request, path: str, params: dict | None = None) -> dict:
    return call_with_refresh(django_request, download, path, params=params)
