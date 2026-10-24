from django.shortcuts import redirect
from django.urls import reverse

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
