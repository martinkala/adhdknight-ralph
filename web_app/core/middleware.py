from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import translation

from core.api_client import SessionExpired


class SessionExpiredMiddleware:
    """Turns core.api_client.SessionExpired (failed token refresh) into a redirect to login?expired=1."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, SessionExpired):
            return redirect(reverse("login") + "?expired=1")
        return None


class LanguageMiddleware:
    """Activates the UI language (constitution B4): `session["language"]` of a logged-in user,
    otherwise the `django_language` cookie (login, registration), otherwise LANGUAGE_CODE (sk)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = get_session_language(request)
        translation.activate(language)
        request.LANGUAGE_CODE = language
        response = self.get_response(request)
        response.headers.setdefault("Content-Language", language)
        return response


def get_session_language(request) -> str:
    supported = {code for code, _ in settings.LANGUAGES}
    for language in (request.session.get("language"), request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)):
        if language in supported:
            return language
    return settings.LANGUAGE_CODE
