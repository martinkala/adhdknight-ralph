import httpx
from django.conf import settings

_TIMEOUT = 5.0


def _url(path: str) -> str:
    return f"{settings.SERVER_URL}{path}"


def post_login(email: str, password: str) -> dict:
    try:
        r = httpx.post(_url("/api/v1/auth/login"), json={"email": email, "password": password}, timeout=_TIMEOUT)
        if r.status_code == 200:
            return r.json()
        return {"error": r.json().get("detail", "Nesprávne prihlasovacie údaje")}
    except httpx.ConnectError:
        return {"error": "server_unavailable"}


def post_register(email: str, password: str, invite_token: str | None = None) -> dict:
    try:
        r = httpx.post(
            _url("/api/v1/auth/register"),
            json={"email": email, "password": password, "invite_token": invite_token or None},
            timeout=_TIMEOUT,
        )
        if r.status_code in (200, 201):
            return r.json()
        if r.status_code == 422:
            return {"error": "invalid_input"}
        return {"error": r.json().get("detail", "Registrácia zlyhala")}
    except httpx.ConnectError:
        return {"error": "server_unavailable"}


def post_refresh(refresh_token: str) -> dict:
    try:
        r = httpx.post(_url("/api/v1/auth/refresh"), json={"refresh_token": refresh_token}, timeout=_TIMEOUT)
        if r.status_code == 200:
            return r.json()
        return {"error": "unauthorized"}
    except httpx.ConnectError:
        return {"error": "server_unavailable"}


class SessionExpired(Exception):
    """The access token was rejected and refreshing it failed; the session is already flushed.
    Handled by core.middleware.SessionExpiredMiddleware (redirect to login?expired=1)."""


def call_with_refresh(request, fn, *args, **kwargs) -> dict:
    """Calls `fn(token, *args, **kwargs)` with the session's access token. On `unauthorized`
    it refreshes the token pair once, stores it in the session and repeats the call.
    If the refresh fails, the session is flushed and SessionExpired is raised."""
    result = fn(request.session.get("token", ""), *args, **kwargs)
    if result.get("error") != "unauthorized":
        return result
    refresh_token = request.session.get("refresh_token")
    refreshed = post_refresh(refresh_token) if refresh_token else {"error": "unauthorized"}
    if refreshed.get("error") == "server_unavailable":
        return refreshed
    if "access_token" not in refreshed:
        request.session.flush()
        raise SessionExpired()
    request.session["token"] = refreshed["access_token"]
    request.session["refresh_token"] = refreshed["refresh_token"]
    result = fn(refreshed["access_token"], *args, **kwargs)
    if result.get("error") == "unauthorized":
        request.session.flush()
        raise SessionExpired()
    return result


def _auth_request(token: str, method: str, path: str, json: dict | None = None) -> dict:
    """Authenticated call returning the JSON body, {} for 204, or {"error": ..., "status_code": ...}
    where error is the API `detail` for 400/403/409 (e.g. "wrong_password")."""
    try:
        r = httpx.request(
            method, _url(path), json=json, headers={"Authorization": f"Bearer {token}"}, timeout=_TIMEOUT
        )
        if r.status_code in (200, 201):
            return r.json()
        if r.status_code == 204:
            return {}
        if r.status_code == 401:
            return {"error": "unauthorized"}
        if r.status_code in (400, 403, 409):
            return {"error": r.json().get("detail", "server_error"), "status_code": r.status_code}
        if r.status_code == 422:
            return {"error": "invalid_input", "status_code": 422}
        return {"error": "server_error", "status_code": r.status_code}
    except (httpx.ConnectError, httpx.TimeoutException):
        return {"error": "server_unavailable"}


def change_password(token: str, old_password: str, new_password: str) -> dict:
    return _auth_request(
        token, "POST", "/api/v1/auth/change-password",
        json={"old_password": old_password, "new_password": new_password},
    )


def delete_account(token: str, password: str) -> dict:
    return _auth_request(token, "DELETE", "/api/v1/user/me", json={"password": password, "confirm": "DELETE"})


def get_user_settings(token: str) -> dict:
    return _auth_request(token, "GET", "/api/v1/user/settings")


def get_history(token: str, days: int = 30) -> dict:
    try:
        r = httpx.get(
            _url(f"/api/v1/user/history?days={days}"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            return r.json()
        if r.status_code == 401:
            return {"error": "unauthorized"}
        return {"error": "server_error"}
    except httpx.ConnectError:
        return {"error": "server_unavailable"}


def get_debug(token: str, days: int = 60) -> dict:
    try:
        r = httpx.get(
            _url(f"/api/v1/user/debug?days={days}"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            return r.json()
        if r.status_code == 401:
            return {"error": "unauthorized"}
        return {"error": "server_error"}
    except httpx.ConnectError:
        return {"error": "server_unavailable"}


def get_me(token: str) -> dict:
    try:
        r = httpx.get(
            _url("/api/v1/user/me"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            return r.json()
        if r.status_code == 401:
            return {"error": "unauthorized"}
        return {"error": "server_error"}
    except httpx.ConnectError:
        return {"error": "server_unavailable"}
