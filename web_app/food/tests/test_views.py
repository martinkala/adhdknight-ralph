from django.test import TestCase
from django.urls import reverse


def _login_session(client):
    session = client.session
    session["user_email"] = "user@example.com"
    session["token"] = "fake-token"
    session.save()


class FoodHomeTests(TestCase):
    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get("/food/")
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    def test_logged_in_sees_food_home(self):
        _login_session(self.client)
        response = self.client.get("/food/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-testid="food-home"')

    def test_base_loads_local_htmx_with_csrf_header(self):
        _login_session(self.client)
        content = self.client.get("/food/").content.decode()
        self.assertIn("/static/js/htmx.min.js", content)
        self.assertIn('hx-headers=\'{"X-CSRFToken": "', content)


class AppSwitchTests(TestCase):
    def _switch_classes(self, html, testid):
        marker = f'data-testid="{testid}" class="'
        start = html.index(marker) + len(marker)
        return html[start:html.index('"', start)].split()

    def test_food_switch_active_on_food(self):
        _login_session(self.client)
        html = self.client.get("/food/").content.decode()
        self.assertIn("active", self._switch_classes(html, "app-switch-food"))
        self.assertNotIn("active", self._switch_classes(html, "app-switch-adhd"))
        # ADHD links only in the ADHD part
        self.assertNotIn(reverse("trend"), html)
        self.assertIn('data-testid="nav-food-home"', html)

    def test_adhd_switch_active_on_dashboard(self):
        from unittest.mock import patch
        _login_session(self.client)
        with patch("core.api_client.get_history", return_value={"days": [], "total_days": 0}):
            html = self.client.get("/").content.decode()
        self.assertIn("active", self._switch_classes(html, "app-switch-adhd"))
        self.assertNotIn("active", self._switch_classes(html, "app-switch-food"))
        self.assertIn(reverse("trend"), html)
        self.assertNotIn('data-testid="nav-food-home"', html)
