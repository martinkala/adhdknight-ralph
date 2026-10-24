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


TODAY = "2026-10-24"


def _day_detail(date="2026-10-20", **values):
    categories = ("breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner", "after_dinner",
                  "unassigned", "medication", "supplement", "sport", "note")
    return {
        "schema_version": "1.0", "id": "d1", "date": date, "updated_at": "2026-10-20T08:00:00Z",
        "sleep_quality": values.get("sleep_quality"), "stool": values.get("stool"), "gas": values.get("gas"),
        "entries": {c: [] for c in categories}, "weights": [], "blood_pressures": [],
        "prev_date": None, "next_date": None,
    }


class FakeApi:
    """Replaces food.api_client.request; `routes` maps (method, path) to a response dict."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, token, method, path, json=None, params=None):
        self.calls.append((method, path, json))
        return self.routes.get((method, path), {"error": "server_error", "status_code": 500})


def _patch_api(routes):
    from unittest.mock import patch
    fake = FakeApi(routes)
    return fake, patch("food.api_client.request", fake)


class FoodNewDayTests(TestCase):
    def setUp(self):
        _login_session(self.client)

    def test_home_has_today_button_and_date_form(self):
        fake, p = _patch_api({("GET", "/today"): {"date": TODAY, "exists": False}})
        with p:
            html = self.client.get("/food/").content.decode()
        self.assertIn('data-testid="open-today"', html)
        self.assertIn('data-testid="new-day-form"', html)
        self.assertIn(f'max="{TODAY}"', html)
        self.assertIn(f'value="{TODAY}"', html)

    def test_future_date_shows_error(self):
        fake, p = _patch_api({
            ("GET", "/today"): {"date": TODAY, "exists": False},
            ("POST", "/days"): {"error": "future_date", "status_code": 422},
        })
        with p:
            response = self.client.post("/food/days/new/", {"date": "2026-10-30"})
        self.assertContains(response, 'data-testid="error-future-date"')
        self.assertIn(("POST", "/days", {"date": "2026-10-30"}), fake.calls)

    def test_existing_day_shows_error_with_link(self):
        fake, p = _patch_api({
            ("GET", "/today"): {"date": TODAY, "exists": True},
            ("POST", "/days"): {"error": "day_exists", "status_code": 409},
        })
        with p:
            response = self.client.post("/food/days/new/", {"date": "2026-10-20"})
        self.assertContains(response, 'data-testid="error-day-exists"')
        self.assertContains(response, 'href="/food/day/2026-10-20/"')

    def test_new_day_redirects_to_day(self):
        fake, p = _patch_api({("POST", "/days"): _day_detail()})
        with p:
            response = self.client.post("/food/days/new/", {"date": "2026-10-20"})
        self.assertRedirects(response, "/food/day/2026-10-20/", fetch_redirect_response=False)

    def test_open_today_creates_missing_day(self):
        fake, p = _patch_api({
            ("GET", "/today"): {"date": TODAY, "exists": False},
            ("POST", "/days"): _day_detail(TODAY),
        })
        with p:
            response = self.client.post("/food/today/")
        self.assertRedirects(response, f"/food/day/{TODAY}/", fetch_redirect_response=False)
        self.assertIn(("POST", "/days", {"date": TODAY}), fake.calls)

    def test_open_today_does_not_create_existing_day(self):
        fake, p = _patch_api({("GET", "/today"): {"date": TODAY, "exists": True}})
        with p:
            response = self.client.post("/food/today/")
        self.assertRedirects(response, f"/food/day/{TODAY}/", fetch_redirect_response=False)
        self.assertNotIn("POST", [c[0] for c in fake.calls])


class FoodDayScreenTests(TestCase):
    def setUp(self):
        _login_session(self.client)

    def test_day_screen_sections_in_order(self):
        fake, p = _patch_api({("GET", "/days/2026-10-20"): _day_detail(sleep_quality=2)})
        with p:
            html = self.client.get("/food/day/2026-10-20/").content.decode()
        order = ["breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner", "after_dinner",
                 "unassigned", "medication", "supplement", "bp", "weight", "digestion", "sleep", "sport", "note"]
        positions = [html.index(f'data-testid="section-{key}"') for key in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('data-testid="prev-day"', html)
        self.assertIn('data-testid="next-day"', html)
        self.assertIn('data-testid="save-status"', html)
        # The selected sleep value clears itself when tapped again.
        start = html.index('data-testid="sleep-2"')
        button = html[html.rindex("<button", 0, start):html.index("</button>", start)]
        self.assertIn('aria-pressed="true"', button)
        self.assertIn('"sleep_quality": ""', button)

    def test_missing_day_is_404_with_create_button(self):
        fake, p = _patch_api({
            ("GET", "/days/2026-10-20"): {"error": "day_not_found", "status_code": 404},
            ("GET", "/today"): {"date": TODAY, "exists": False},
        })
        with p:
            response = self.client.get("/food/day/2026-10-20/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'data-testid="create-day"', status_code=404)

    def test_missing_future_day_has_no_create_button(self):
        fake, p = _patch_api({
            ("GET", "/days/2026-10-30"): {"error": "day_not_found", "status_code": 404},
            ("GET", "/today"): {"date": TODAY, "exists": False},
        })
        with p:
            response = self.client.get("/food/day/2026-10-30/")
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, 'data-testid="create-day"', status_code=404)

    def test_values_autosave_patches_api(self):
        fake, p = _patch_api({("PATCH", "/days/2026-10-20"): _day_detail(stool=4)})
        with p:
            response = self.client.patch("/food/day/2026-10-20/values/", "stool=4",
                                         content_type="application/x-www-form-urlencoded")
        self.assertEqual(response.status_code, 200)
        self.assertIn(("PATCH", "/days/2026-10-20", {"stool": 4}), fake.calls)
        self.assertContains(response, 'data-testid="save-status"')
        self.assertContains(response, "Saved")

    def test_values_empty_clears(self):
        fake, p = _patch_api({("PATCH", "/days/2026-10-20"): _day_detail()})
        with p:
            self.client.patch("/food/day/2026-10-20/values/", "sleep_quality=",
                              content_type="application/x-www-form-urlencoded")
        self.assertIn(("PATCH", "/days/2026-10-20", {"sleep_quality": None}), fake.calls)


class FoodDeleteDayTests(TestCase):
    def setUp(self):
        _login_session(self.client)

    def test_delete_without_matching_date_does_not_delete(self):
        for confirm in ("", "2026-10-21", "20. 10. 2026"):
            fake, p = _patch_api({("DELETE", "/days/2026-10-20"): {}})
            with p:
                response = self.client.post("/food/day/2026-10-20/delete/", {"confirm_date": confirm})
            self.assertRedirects(response, "/food/day/2026-10-20/", fetch_redirect_response=False)
            self.assertEqual(fake.calls, [])

    def test_delete_with_matching_date(self):
        fake, p = _patch_api({("DELETE", "/days/2026-10-20"): {}})
        with p:
            response = self.client.post("/food/day/2026-10-20/delete/", {"confirm_date": "2026-10-20"})
        self.assertRedirects(response, "/food/", fetch_redirect_response=False)
        self.assertEqual(fake.calls, [("DELETE", "/days/2026-10-20", None)])

    def test_delete_requires_post(self):
        response = self.client.get("/food/day/2026-10-20/delete/")
        self.assertEqual(response.status_code, 405)
