import json

from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods, require_POST
from django.urls import reverse
from core import api_client

_ERROR_MESSAGES = {
    "server_unavailable": "Server nie je dostupný. Skúste neskôr.",
    "server_error": "Načítanie dát zlyhalo. Skúste to znova.",
}

_REGISTER_ERRORS = {
    "invite_required": "Registrácia je možná iba na pozvánku.",
    "invite_invalid": "Pozvánka je neplatná, expirovala alebo už bola použitá. Požiadajte o novú.",
    "Email already registered": "Tento e-mail je už zaregistrovaný.",
    "invalid_input": "Zadajte platný e-mail a heslo s aspoň 8 znakmi.",
    "server_unavailable": "Server nie je dostupný. Skúste neskôr.",
}

_ACCOUNT_ERRORS = {
    "wrong_password": "Nesprávne heslo.",
    "invalid_input": "Nové heslo musí mať aspoň 8 znakov.",
    "server_unavailable": "Server nie je dostupný. Skúste neskôr.",
}


def _require_login(request):
    return request.session.get("user_email") and request.session.get("token")


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
            request.session["refresh_token"] = result.get("refresh_token")
            user_settings = api_client.get_user_settings(result["access_token"])
            request.session["language"] = user_settings.get("language", "sk")
            return redirect("dashboard")
        error = result.get("error", "Prihlásenie zlyhalo")
        if error == "server_unavailable":
            error = "Server nie je dostupný. Skúste neskôr."
    return render(request, "login.html", {"error": error})


def register_view(request):
    """Invite-only registration (food-002): the invitation token comes from the link
    `/register/?invite=<token>` and travels in a hidden field."""
    if _require_login(request):
        return redirect("dashboard")
    error = None
    success = None
    invite = (request.POST.get("invite") or request.GET.get("invite") or "").strip()
    if request.method == "POST" and invite:
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        result = api_client.post_register(email, password, invite)
        if "access_token" in result or result.get("email"):
            success = "Účet bol vytvorený. Teraz sa môžete prihlásiť."
        else:
            error = result.get("error", "Registrácia zlyhala")
            error = _REGISTER_ERRORS.get(error, error)
    return render(request, "register.html", {"error": error, "success": success, "invite": invite})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    request.session.flush()
    return redirect("login")


def dashboard(request):
    if not _require_login(request):
        return redirect("login")
    history = api_client.call_with_refresh(request, api_client.get_history, days=30)
    return render(request, "dashboard.html", _history_context(history))


def trend(request):
    if not _require_login(request):
        return redirect("login")
    history = api_client.call_with_refresh(request, api_client.get_history, days=60)
    return render(request, "trend.html", _history_context(history))


def account(request):
    if not _require_login(request):
        return redirect("login")
    me = api_client.call_with_refresh(request, api_client.get_me)
    return render(request, "account.html", {"me": me})


@require_POST
def change_password_view(request):
    if not _require_login(request):
        return redirect("login")
    result = api_client.call_with_refresh(
        request, api_client.change_password,
        request.POST.get("old_password", ""), request.POST.get("new_password", ""),
    )
    if result.get("error"):
        messages.error(request, _ACCOUNT_ERRORS.get(result["error"], _ERROR_MESSAGES["server_error"]))
    else:
        messages.success(request, "Heslo bolo zmenené.")
    return redirect("account")


@require_POST
def delete_account_view(request):
    """Deletes the whole shared account, i.e. ADHD and Food data (constitution B5)."""
    if not _require_login(request):
        return redirect("login")
    if request.POST.get("confirm") != "on":
        messages.error(request, "Potvrďte, že chcete zmazať účet so všetkými dátami.")
        return redirect("account")
    result = api_client.call_with_refresh(request, api_client.delete_account, request.POST.get("password", ""))
    if result.get("error"):
        messages.error(request, _ACCOUNT_ERRORS.get(result["error"], _ERROR_MESSAGES["server_error"]))
        return redirect("account")
    request.session.flush()
    return redirect(reverse("login") + "?deleted=1")


def info(request):
    return render(request, "info.html")


def debug_view(request):
    if not _require_login(request):
        return redirect("login")
    debug = api_client.call_with_refresh(request, api_client.get_debug, days=60)
    return render(request, "debug.html", {"debug": debug})
