import json

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from core import api_client

_LOGIN_EXPIRED = "?expired=1"

_ERROR_MESSAGES = {
    "server_unavailable": "Server nie je dostupný. Skúste neskôr.",
    "server_error": "Načítanie dát zlyhalo. Skúste to znova.",
}


def _require_login(request):
    return request.session.get("user_email") and request.session.get("token")


def _expired_redirect():
    return redirect(reverse("login") + _LOGIN_EXPIRED)


def _history_context(history: dict) -> dict:
    """Builds the template context for a history-backed page (FR-001/FR-002):
    distinguishes a load failure from genuinely-empty history, and serializes
    `days` as real JSON so it can be safely embedded in an inline <script>
    (Django's `{{ }}` on a Python list/dict emits `repr()`-style output —
    e.g. `None` instead of `null` — which is not valid JavaScript)."""
    error = history.get("error")
    if error:
        return {"error_message": _ERROR_MESSAGES.get(error, error), "has_data": False, "days_json": "[]"}
    days = history.get("days", [])
    return {"error_message": None, "has_data": bool(days), "days_json": json.dumps(days)}


def login_view(request):
    if _require_login(request):
        return redirect("dashboard")
    error = None
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        result = api_client.post_login(email, password)
        if "access_token" in result:
            request.session["user_email"] = email
            request.session["token"] = result["access_token"]
            return redirect("dashboard")
        error = result.get("error", "Prihlásenie zlyhalo")
        if error == "server_unavailable":
            error = "Server nie je dostupný. Skúste neskôr."
    return render(request, "login.html", {"error": error})


def register_view(request):
    if _require_login(request):
        return redirect("dashboard")
    error = None
    success = None
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        result = api_client.post_register(email, password)
        if "access_token" in result or result.get("email"):
            success = "Účet bol vytvorený. Teraz sa môžete prihlásiť."
        else:
            error = result.get("error", "Registrácia zlyhala")
            if error == "server_unavailable":
                error = "Server nie je dostupný. Skúste neskôr."
    return render(request, "register.html", {"error": error, "success": success})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    request.session.flush()
    return redirect("login")


def dashboard(request):
    if not _require_login(request):
        return redirect("login")
    token = request.session["token"]
    history = api_client.get_history(token, days=30)
    if history.get("error") == "unauthorized":
        request.session.flush()
        return _expired_redirect()
    return render(request, "dashboard.html", _history_context(history))


def trend(request):
    if not _require_login(request):
        return redirect("login")
    token = request.session["token"]
    history = api_client.get_history(token, days=60)
    if history.get("error") == "unauthorized":
        request.session.flush()
        return _expired_redirect()
    return render(request, "trend.html", _history_context(history))


def account(request):
    if not _require_login(request):
        return redirect("login")
    token = request.session["token"]
    me = api_client.get_me(token)
    if me.get("error") == "unauthorized":
        request.session.flush()
        return _expired_redirect()
    return render(request, "account.html", {"me": me})


def info(request):
    return render(request, "info.html")


def debug_view(request):
    if not _require_login(request):
        return redirect("login")
    token = request.session["token"]
    debug = api_client.get_debug(token, days=60)
    if debug.get("error") == "unauthorized":
        request.session.flush()
        return _expired_redirect()
    return render(request, "debug.html", {"debug": debug})
