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


def post_register(email: str, password: str) -> dict:
    try:
        r = httpx.post(_url("/api/v1/auth/register"), json={"email": email, "password": password}, timeout=_TIMEOUT)
        if r.status_code in (200, 201):
            return r.json()
        return {"error": r.json().get("detail", "Registrácia zlyhala")}
    except httpx.ConnectError:
        return {"error": "server_unavailable"}


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
