"""food-002: token refresh in the session, 30-day session, invite-only registration,
change password and account deletion in the web console. httpx is mocked."""
from unittest.mock import patch

import httpx
from django.conf import settings
from django.test import TestCase
from django.urls import reverse


def _response(status_code: int, json=None) -> httpx.Response:
    request = httpx.Request("GET", "http://api.test")
    if json is None:
        return httpx.Response(status_code, request=request)
    return httpx.Response(status_code, json=json, request=request)


def _login_session(client, refresh_token="old-refresh"):
    session = client.session
    session["user_email"] = "user@example.com"
    session["token"] = "old-access"
    if refresh_token:
        session["refresh_token"] = refresh_token
    session.save()


TOKENS = {"access_token": "new-access", "refresh_token": "new-refresh", "token_type": "bearer", "expires_in": 900}
HISTORY = {"schema_version": "1.0", "days": [], "total_days": 0}


class RefreshTests(TestCase):
    def test_401_then_successful_refresh_repeats_call_and_stores_tokens(self):
        _login_session(self.client)
        seen_tokens = []

        def fake_get(url, headers=None, timeout=None):
            token = headers["Authorization"].split()[1]
            seen_tokens.append(token)
            return _response(200, HISTORY) if token == "new-access" else _response(401, {"detail": "expired"})

        with patch("core.api_client.httpx.get", side_effect=fake_get), \
                patch("core.api_client.httpx.post", return_value=_response(200, TOKENS)) as post:
            response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(seen_tokens, ["old-access", "new-access"])
        self.assertTrue(post.call_args.args[0].endswith("/api/v1/auth/refresh"))
        self.assertEqual(post.call_args.kwargs["json"], {"refresh_token": "old-refresh"})
        self.assertEqual(self.client.session["token"], "new-access")
        self.assertEqual(self.client.session["refresh_token"], "new-refresh")

    def test_401_and_failed_refresh_logs_out(self):
        _login_session(self.client)
        with patch("core.api_client.httpx.get", return_value=_response(401, {"detail": "expired"})), \
                patch("core.api_client.httpx.post", return_value=_response(401, {"detail": "expired"})):
            response = self.client.get(reverse("dashboard"))

        self.assertRedirects(response, reverse("login") + "?expired=1", fetch_redirect_response=False)
        self.assertNotIn("token", self.client.session)
        self.assertNotIn("refresh_token", self.client.session)
        self.assertNotIn("user_email", self.client.session)

    def test_refresh_applies_to_all_adhd_views(self):
        for name in ("trend", "debug", "account"):
            with self.subTest(view=name):
                _login_session(self.client)

                def fake_get(url, headers=None, timeout=None):
                    if headers["Authorization"] == "Bearer new-access":
                        body = {"email": "user@example.com", "created_at": "2026-10-01T00:00:00Z", "total_days": 0,
                                "app_id": "adhd_tracker", "days_with_index": 0, **HISTORY}
                        return _response(200, body)
                    return _response(401, {"detail": "expired"})

                with patch("core.api_client.httpx.get", side_effect=fake_get), \
                        patch("core.api_client.httpx.post", return_value=_response(200, TOKENS)):
                    response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self.client.session["token"], "new-access")

    def test_food_client_refreshes_too(self):
        from food import api_client as food_api

        _login_session(self.client)
        request = self.client.get(reverse("food:home")).wsgi_request

        def fake_request(method, url, json=None, params=None, headers=None, timeout=None):
            if headers["Authorization"] == "Bearer new-access":
                return _response(200, {"ok": True})
            return _response(401, {"detail": "expired"})

        with patch("food.api_client.httpx.request", side_effect=fake_request), \
                patch("core.api_client.httpx.post", return_value=_response(200, TOKENS)):
            result = food_api.call(request, "GET", "/days")
        self.assertEqual(result, {"ok": True})
        self.assertEqual(request.session["token"], "new-access")


class LoginSessionTests(TestCase):
    def test_login_stores_refresh_token_and_language(self):
        def fake_request(method, url, json=None, headers=None, timeout=None):
            self.assertTrue(url.endswith("/api/v1/user/settings"))
            return _response(200, {"schema_version": "1.0", "language": "cs", "timezone": "Europe/Bratislava"})

        with patch("core.api_client.httpx.post", return_value=_response(200, TOKENS)), \
                patch("core.api_client.httpx.request", side_effect=fake_request):
            response = self.client.post(reverse("login"), {"email": "user@example.com", "password": "secret123"})

        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)
        session = self.client.session
        self.assertEqual(session["token"], "new-access")
        self.assertEqual(session["refresh_token"], "new-refresh")
        self.assertEqual(session["user_email"], "user@example.com")
        self.assertEqual(session["language"], "cs")

    def test_session_lasts_30_days_and_is_extended(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 30 * 24 * 3600)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)


class RegisterTests(TestCase):
    def test_without_invite_shows_info_and_no_form(self):
        response = self.client.get(reverse("register"))
        self.assertContains(response, 'data-testid="invite-required"')
        self.assertNotContains(response, 'data-testid="register-email"')

    def test_invite_is_kept_in_hidden_field(self):
        response = self.client.get(reverse("register") + "?invite=abc123")
        self.assertContains(response, 'name="invite" value="abc123"')
        self.assertContains(response, 'data-testid="register-email"')

    def test_post_sends_invite_token(self):
        with patch("core.api_client.httpx.post", return_value=_response(201, TOKENS)) as post:
            response = self.client.post(
                reverse("register"), {"email": "new@example.com", "password": "secret123", "invite": "abc123"}
            )
        self.assertContains(response, 'data-testid="register-success"')
        self.assertEqual(post.call_args.kwargs["json"]["invite_token"], "abc123")

    def test_invalid_invite_message(self):
        with patch("core.api_client.httpx.post", return_value=_response(403, {"detail": "invite_invalid"})):
            response = self.client.post(
                reverse("register"), {"email": "new@example.com", "password": "secret123", "invite": "bad"}
            )
        self.assertContains(response, "Pozvánka je neplatná")

    def test_invite_required_message_from_api(self):
        with patch("core.api_client.httpx.post", return_value=_response(403, {"detail": "invite_required"})):
            response = self.client.post(
                reverse("register"), {"email": "new@example.com", "password": "secret123", "invite": "x"}
            )
        self.assertContains(response, "Registrácia je možná iba na pozvánku.")

    def test_post_without_invite_does_not_call_api(self):
        with patch("core.api_client.httpx.post") as post:
            response = self.client.post(reverse("register"), {"email": "new@example.com", "password": "secret123"})
        post.assert_not_called()
        self.assertContains(response, 'data-testid="invite-required"')


ME = {"email": "user@example.com", "created_at": "2026-10-01T00:00:00Z", "total_days": 3}


class ChangePasswordTests(TestCase):
    def test_success_calls_api_and_shows_message(self):
        _login_session(self.client)
        with patch("core.api_client.httpx.request", return_value=_response(204)) as req, \
                patch("core.api_client.httpx.get", return_value=_response(200, ME)):
            response = self.client.post(
                reverse("change_password"), {"old_password": "secret123", "new_password": "new-secret-456"},
                follow=True,
            )
        method, url = req.call_args.args
        self.assertEqual(method, "POST")
        self.assertTrue(url.endswith("/api/v1/auth/change-password"))
        self.assertEqual(req.call_args.kwargs["json"], {"old_password": "secret123", "new_password": "new-secret-456"})
        self.assertContains(response, "Heslo bolo zmenené.")
        self.assertContains(response, 'data-testid="change-password-form"')

    def test_wrong_password_message(self):
        _login_session(self.client)
        with patch("core.api_client.httpx.request", return_value=_response(400, {"detail": "wrong_password"})), \
                patch("core.api_client.httpx.get", return_value=_response(200, ME)):
            response = self.client.post(
                reverse("change_password"), {"old_password": "nope", "new_password": "new-secret-456"}, follow=True,
            )
        self.assertContains(response, "Nesprávne heslo.")


class DeleteAccountTests(TestCase):
    def test_account_page_warns_about_all_apps(self):
        _login_session(self.client)
        with patch("core.api_client.httpx.get", return_value=_response(200, ME)):
            response = self.client.get(reverse("account"))
        self.assertContains(response, 'data-testid="delete-account"')
        self.assertContains(response, "všetky dáta ADHD aj Food")

    def test_success_flushes_session(self):
        _login_session(self.client)
        with patch("core.api_client.httpx.request", return_value=_response(204)) as req:
            response = self.client.post(reverse("delete_account"), {"password": "secret123", "confirm": "on"})
        method, url = req.call_args.args
        self.assertEqual(method, "DELETE")
        self.assertTrue(url.endswith("/api/v1/user/me"))
        self.assertEqual(req.call_args.kwargs["json"], {"password": "secret123", "confirm": "DELETE"})
        self.assertRedirects(response, reverse("login") + "?deleted=1", fetch_redirect_response=False)
        self.assertNotIn("token", self.client.session)
        self.assertNotIn("user_email", self.client.session)

    def test_without_confirmation_does_not_call_api(self):
        _login_session(self.client)
        with patch("core.api_client.httpx.request") as req:
            response = self.client.post(reverse("delete_account"), {"password": "secret123"})
        req.assert_not_called()
        self.assertRedirects(response, reverse("account"), fetch_redirect_response=False)
        self.assertIn("token", self.client.session)

    def test_wrong_password_keeps_session(self):
        _login_session(self.client)
        with patch("core.api_client.httpx.request", return_value=_response(400, {"detail": "wrong_password"})), \
                patch("core.api_client.httpx.get", return_value=_response(200, ME)):
            response = self.client.post(
                reverse("delete_account"), {"password": "nope", "confirm": "on"}, follow=True
            )
        self.assertContains(response, "Nesprávne heslo.")
        self.assertIn("token", self.client.session)
