import json

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import translation
from django.utils.translation import gettext as _, gettext_lazy
from django.views.decorators.http import require_http_methods, require_POST
from django.urls import reverse
from core import api_client

_ERROR_MESSAGES = {
    "server_unavailable": gettext_lazy("Server is not available. Try again later."),
    "server_error": gettext_lazy("Loading data failed. Try again."),
}

_LOGIN_ERRORS = {
    "Invalid credentials": gettext_lazy("Wrong e-mail or password."),
    "server_unavailable": _ERROR_MESSAGES["server_unavailable"],
}

_REGISTER_ERRORS = {
    "invite_required": gettext_lazy("Registration is possible only by invitation."),
    "invite_invalid": gettext_lazy("The invitation is invalid, expired or already used. Ask for a new one."),
    "Email already registered": gettext_lazy("This e-mail is already registered."),
    "invalid_input": gettext_lazy("Enter a valid e-mail and a password with at least 8 characters."),
    "server_unavailable": _ERROR_MESSAGES["server_unavailable"],
}

_ACCOUNT_ERRORS = {
    "wrong_password": gettext_lazy("Wrong password."),
    "invalid_input": gettext_lazy("The new password must have at least 8 characters."),
    "server_unavailable": _ERROR_MESSAGES["server_unavailable"],
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
        return {"error_message": str(_ERROR_MESSAGES.get(error, error)), "has_data": False, "days_json": "[]"}
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
            request.session["language"] = user_settings.get("language", settings.LANGUAGE_CODE)
            response = redirect("dashboard")
            _set_language_cookie(response, request.session["language"])
            return response
        error = _LOGIN_ERRORS.get(result.get("error"), _("Login failed."))
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
            success = _("The account was created. You can log in now.")
        else:
            error = _REGISTER_ERRORS.get(result.get("error"), _("Registration failed."))
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
    me_error = str(_ERROR_MESSAGES.get(me["error"], _ERROR_MESSAGES["server_error"])) if me.get("error") else None
    return render(request, "account.html", {"me": me, "me_error": me_error})


def _set_language_cookie(response, language: str):
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME, language, max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH, samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )


@require_POST
def change_language_view(request):
    """Saves the UI language in the account (users.language), the session and the cookie (food-010 FR-3)."""
    if not _require_login(request):
        return redirect("login")
    language = request.POST.get("language", "")
    if language not in dict(settings.LANGUAGES):
        messages.error(request, _("Choose a language."))
        return redirect("account")
    result = api_client.call_with_refresh(request, api_client.update_user_settings, language=language)
    if result.get("error"):
        messages.error(request, _ACCOUNT_ERRORS.get(result["error"], _ERROR_MESSAGES["server_error"]))
        return redirect("account")
    request.session["language"] = language
    translation.activate(language)
    messages.success(request, _("The language was changed."))
    response = redirect("account")
    _set_language_cookie(response, language)
    return response


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
        messages.success(request, _("The password was changed."))
    return redirect("account")


@require_POST
def delete_account_view(request):
    """Deletes the whole shared account, i.e. ADHD and Food data (constitution B5)."""
    if not _require_login(request):
        return redirect("login")
    if request.POST.get("confirm") != "on":
        messages.error(request, _("Confirm that you want to delete the account with all its data."))
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
