from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


def _login_session(client):
    session = client.session
    session["user_email"] = "user@example.com"
    session["token"] = "fake-token"
    session.save()


class DashboardHistoryTests(TestCase):
    """Regression coverage for the dashboard/trend "no data" bug: the view used to
    embed the API's response as Python repr (`None`, single-quoted strings) into an
    inline <script>, which is invalid JavaScript and silently broke the chart."""

    def test_user_with_data_sees_chart_json(self):
        _login_session(self.client)
        history = {
            "days": [{"date": "2026-08-01", "index_value": None, "detail": []},
                      {"date": "2026-08-02", "index_value": 42.5, "detail": []}],
            "total_days": 2,
        }
        with patch("core.api_client.get_history", return_value=history):
            response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertNotIn("Zatiaľ nemáte", content)
        # Valid JSON embed: null, not the Python repr `None`.
        self.assertIn('"index_value": null', content)
        self.assertNotIn("None", content)

    def test_user_without_data_sees_empty_state(self):
        _login_session(self.client)
        with patch("core.api_client.get_history", return_value={"days": [], "total_days": 0}):
            response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Zatiaľ nemáte žiadne dáta.", response.content.decode())

    def test_expired_token_redirects_to_login(self):
        _login_session(self.client)
        with patch("core.api_client.get_history", return_value={"error": "unauthorized"}):
            response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("login") + "?expired=1")
        self.assertNotIn("token", self.client.session)

    def test_server_error_shows_distinct_message_from_empty_data(self):
        _login_session(self.client)
        with patch("core.api_client.get_history", return_value={"error": "server_error"}):
            response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertNotIn("Zatiaľ nemáte žiadne dáta.", content)
        self.assertIn("alert-error", content)

    def test_trend_view_serializes_data_as_valid_json_too(self):
        _login_session(self.client)
        history = {"days": [{"date": "2026-08-01", "index_value": None, "detail": []}], "total_days": 1}
        with patch("core.api_client.get_history", return_value=history):
            response = self.client.get(reverse("trend"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('"index_value": null', content)
        self.assertNotIn("None", content)
