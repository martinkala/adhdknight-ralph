from django.test import Client, TestCase
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
        self.params = []

    def __call__(self, token, method, path, json=None, params=None):
        self.calls.append((method, path, json))
        self.params.append(params)
        return self.routes.get((method, path), {"error": "server_error", "status_code": 500})


def _patch_api(routes):
    from unittest.mock import patch
    fake = FakeApi(routes)
    return fake, patch("food.api_client.request", fake)


def _calendar(month, days=(), today=TODAY):
    return {"schema_version": "1.0", "month": month, "today": today, "days": list(days)}


class FoodNewDayTests(TestCase):
    def setUp(self):
        _login_session(self.client)

    def test_home_has_today_button_and_date_form(self):
        fake, p = _patch_api({("GET", "/calendar"): _calendar("2026-10")})
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

    def test_calendar_tap_on_existing_day_opens_it(self):
        fake, p = _patch_api({("POST", "/days"): {"error": "day_exists", "status_code": 409}})
        with p:
            response = self.client.post("/food/days/new/", {"date": "2026-10-20", "open_existing": "1"})
        self.assertRedirects(response, "/food/day/2026-10-20/", fetch_redirect_response=False)

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
        self.assertRedirects(response, "/food/?month=2026-10", fetch_redirect_response=False)
        self.assertEqual(fake.calls, [("DELETE", "/days/2026-10-20", None)])

    def test_delete_requires_post(self):
        response = self.client.get("/food/day/2026-10-20/delete/")
        self.assertEqual(response.status_code, 405)


def _entry(text, quantity=None, unit=None, intensity=None, entry_id="e1", category="breakfast"):
    return {"id": entry_id, "category": category, "text": text, "text_norm": text.lower(), "quantity": quantity, "unit": unit,
            "intensity": intensity, "position": 0, "updated_at": "2026-10-20T08:00:00Z"}


def _detail_with(**lists):
    detail = _day_detail()
    for key, value in lists.items():
        if key in ("weights", "blood_pressures"):
            detail[key] = value
        else:
            detail["entries"][key] = value
    return detail


class FoodEntriesTests(TestCase):
    def setUp(self):
        _login_session(self.client)

    def test_day_screen_has_add_fields_and_entries(self):
        detail = _detail_with(breakfast=[_entry("toasty", 2), _entry("kofola", 0.5, "l", entry_id="e2")],
                              sport=[_entry("eBike", intensity=3, entry_id="e3", category="sport")])
        fake, p = _patch_api({("GET", "/days/2026-10-20"): detail})
        with p:
            html = self.client.get("/food/day/2026-10-20/").content.decode()
        for key in ("breakfast", "unassigned", "meds", "sport", "note", "bp", "weight"):
            self.assertIn(f'data-testid="add-{key}"', html)
        self.assertIn("2×", html)
        self.assertIn("0.5 l", html)
        self.assertIn('data-testid="entry-intensity"', html)
        self.assertIn('<option value="3" selected>', html)
        self.assertIn('hx-delete="/food/day/2026-10-20/entries/breakfast/e1/"', html)

    def test_add_entries_posts_and_renders_section(self):
        fake, p = _patch_api({
            ("POST", "/days/2026-10-20/entries"): {"created": []},
            ("GET", "/days/2026-10-20"): _detail_with(breakfast=[_entry("toasty", 2), _entry("kafe", entry_id="e2")]),
        })
        with p:
            response = self.client.post("/food/day/2026-10-20/entries/breakfast/", {"text": "2 toasty, kafe"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("X-Food-Error", response)
        self.assertIn(("POST", "/days/2026-10-20/entries", {"category": "breakfast", "text": "2 toasty, kafe"}),
                      fake.calls)
        html = response.content.decode()
        self.assertIn('id="entries-breakfast"', html)
        self.assertEqual(html.count('data-testid="entry"'), 2)
        self.assertIn('data-testid="entry-qty-add"', html)

    def test_add_error_is_shown_with_header(self):
        fake, p = _patch_api({
            ("POST", "/days/2026-10-20/entries"): {"error": "empty_text", "status_code": 422},
            ("GET", "/days/2026-10-20"): _day_detail(),
        })
        with p:
            response = self.client.post("/food/day/2026-10-20/entries/lunch/", {"text": " , "})
        self.assertEqual(response["X-Food-Error"], "empty_text")
        self.assertContains(response, 'data-testid="entry-error"')

    def test_unknown_category_is_404(self):
        response = self.client.post("/food/day/2026-10-20/entries/brunch/", {"text": "x"})
        self.assertEqual(response.status_code, 404)

    def test_patch_entry_text_quantity_intensity(self):
        routes = {("PATCH", "/entries/e1"): _entry("x"), ("GET", "/days/2026-10-20"): _day_detail()}
        cases = [
            ("text=nove+jedlo", {"text": "nove jedlo"}),
            ("quantity=0%2C5&unit=l", {"quantity": 0.5, "unit": "l"}),
            ("quantity=2&unit=", {"quantity": 2.0, "unit": None}),
            ("quantity=", {"quantity": None, "unit": None}),
            ("intensity=4", {"intensity": 4}),
            ("intensity=", {"intensity": None}),
        ]
        for body, payload in cases:
            fake, p = _patch_api(routes)
            with p:
                response = self.client.patch("/food/day/2026-10-20/entries/sport/e1/", body,
                                             content_type="application/x-www-form-urlencoded")
            self.assertEqual(response.status_code, 200)
            self.assertIn(("PATCH", "/entries/e1", payload), fake.calls)

    def test_patch_invalid_quantity_does_not_call_api(self):
        fake, p = _patch_api({("GET", "/days/2026-10-20"): _day_detail()})
        with p:
            response = self.client.patch("/food/day/2026-10-20/entries/lunch/e1/", "quantity=abc",
                                         content_type="application/x-www-form-urlencoded")
        self.assertEqual(response["X-Food-Error"], "invalid_quantity")
        self.assertNotIn("PATCH", [c[0] for c in fake.calls])

    def test_delete_entry(self):
        fake, p = _patch_api({("DELETE", "/entries/e1"): {}, ("GET", "/days/2026-10-20"): _day_detail()})
        with p:
            response = self.client.delete("/food/day/2026-10-20/entries/lunch/e1/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(("DELETE", "/entries/e1", None), fake.calls)

    def test_quantity_popover_lists_options(self):
        fake, p = _patch_api({("GET", "/quantities"): {"options": [
            {"quantity": 2.0, "unit": None, "count": 3}, {"quantity": 0.5, "unit": "l", "count": 1}]}})
        with p:
            response = self.client.get("/food/day/2026-10-20/entries/breakfast/e1/quantities/", {"text": "toasty"})
        html = response.content.decode()
        self.assertIn('data-testid="qty-popover"', html)
        self.assertEqual(html.count('data-testid="qty-option"'), 2)
        self.assertLess(html.index("2×"), html.index("0.5 l"))
        self.assertIn('data-testid="qty-none"', html)
        self.assertIn('data-testid="qty-input"', html)


class FoodMeasurementsViewTests(TestCase):
    def setUp(self):
        _login_session(self.client)

    def test_add_blood_pressure_fills_time(self):
        bp = {"id": "b1", "systolic": 130, "diastolic": 85, "pulse": 72, "measured_at": "07:30", "note": None,
              "updated_at": "2026-10-20T08:00:00Z"}
        fake, p = _patch_api({
            ("POST", "/days/2026-10-20/blood-pressures"): bp,
            ("GET", "/days/2026-10-20"): _detail_with(blood_pressures=[bp]),
        })
        with p:
            response = self.client.post("/food/day/2026-10-20/blood-pressures/", {"raw": "130/85 72 7:30"})
        self.assertIn(("POST", "/days/2026-10-20/blood-pressures", {"raw": "130/85 72 7:30", "fill_time": True}),
                      fake.calls)
        html = response.content.decode()
        self.assertIn("130/85", html)
        self.assertIn("07:30", html)
        self.assertIn('value="130/85 72 07:30"', html)

    def test_blood_pressure_error(self):
        fake, p = _patch_api({
            ("POST", "/days/2026-10-20/blood-pressures"): {"error": "bp_range", "status_code": 422},
            ("GET", "/days/2026-10-20"): _day_detail(),
        })
        with p:
            response = self.client.post("/food/day/2026-10-20/blood-pressures/", {"raw": "145/02"})
        self.assertEqual(response["X-Food-Error"], "bp_range")
        self.assertContains(response, 'data-testid="bp-error"')

    def test_add_weight_accepts_comma(self):
        fake, p = _patch_api({
            ("POST", "/days/2026-10-20/weights"): {},
            ("GET", "/days/2026-10-20"): _day_detail(),
        })
        with p:
            self.client.post("/food/day/2026-10-20/weights/", {"kg": "80,6", "measured_at": ""})
        self.assertIn(("POST", "/days/2026-10-20/weights", {"kg": 80.6, "measured_at": None, "note": ""}),
                      fake.calls)

    def test_add_weight_invalid(self):
        fake, p = _patch_api({("GET", "/days/2026-10-20"): _day_detail()})
        with p:
            response = self.client.post("/food/day/2026-10-20/weights/", {"kg": "abc"})
        self.assertEqual(response["X-Food-Error"], "weight_range")
        self.assertContains(response, 'data-testid="weight-error"')

    def test_patch_and_delete_measurements(self):
        fake, p = _patch_api({
            ("PATCH", "/blood-pressures/b1"): {}, ("DELETE", "/weights/w1"): {},
            ("GET", "/days/2026-10-20"): _day_detail(),
        })
        with p:
            self.client.patch("/food/day/2026-10-20/blood-pressures/b1/", "raw=120%2F80&note=ok",
                              content_type="application/x-www-form-urlencoded")
            self.client.delete("/food/day/2026-10-20/weights/w1/")
        self.assertIn(("PATCH", "/blood-pressures/b1", {"raw": "120/80", "note": "ok"}), fake.calls)
        self.assertIn(("DELETE", "/weights/w1", None), fake.calls)


class QtyFilterTests(TestCase):
    def test_labels(self):
        from food.templatetags.food_format import qty, number
        self.assertEqual(qty({"quantity": 2.0, "unit": None}), "2×")
        self.assertEqual(qty({"quantity": 200.0, "unit": "g"}), "200 g")
        self.assertEqual(qty({"quantity": None, "unit": None}), "")
        self.assertEqual(number(80.6), "80.6")
        from django.utils import translation
        with translation.override("sk"):
            self.assertEqual(qty({"quantity": 0.5, "unit": "l"}), "0,5 l")


class FoodSuggestionsViewTests(TestCase):
    def setUp(self):
        _login_session(self.client)

    def _get(self, params, api_result):
        from unittest.mock import patch
        calls = []

        def fake(token, method, path, json=None, params=None):
            calls.append((method, path, params))
            return api_result

        with patch("food.api_client.request", fake):
            response = self.client.get("/food/suggestions/", params)
        return response, calls

    def test_proxies_api_suggestions(self):
        response, calls = self._get({"group": "food", "q": "to", "limit": "8"},
                                    {"suggestions": [{"text": "toasty", "count": 3}]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"suggestions": [{"text": "toasty", "count": 3}]})
        self.assertEqual(calls, [("GET", "/suggestions", {"group": "food", "q": "to", "limit": 8})])

    def test_limit_is_clamped_and_defaults(self):
        _, calls = self._get({"group": "meds", "limit": "500"}, {"suggestions": []})
        self.assertEqual(calls[0][2], {"group": "meds", "q": "", "limit": 20})
        _, calls = self._get({"group": "sport", "limit": "x"}, {"suggestions": []})
        self.assertEqual(calls[0][2]["limit"], 10)

    def test_unknown_group_and_api_error_give_empty_list(self):
        response, calls = self._get({"group": "note", "q": "x"}, {"suggestions": [{"text": "x", "count": 1}]})
        self.assertEqual(response.json(), {"suggestions": []})
        self.assertEqual(calls, [])
        response, _ = self._get({"group": "food", "q": "x"}, {"error": "server_unavailable"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"suggestions": []})

    def test_anonymous_is_401(self):
        response = Client().get("/food/suggestions/", {"group": "food"})
        self.assertEqual(response.status_code, 401)

    def test_day_screen_inputs_have_suggest_groups(self):
        detail = _detail_with(lunch=[_entry("ryza", category="lunch")], note=[_entry("unava", category="note", entry_id="n1")])
        fake, p = _patch_api({("GET", "/days/2026-10-20"): detail})
        with p:
            html = self.client.get("/food/day/2026-10-20/").content.decode()
        self.assertIn('data-testid="add-breakfast"\n               data-suggest="food"', html)
        self.assertIn('data-testid="add-meds"\n               data-suggest="meds"', html)
        self.assertIn('data-testid="add-sport"\n               data-suggest="sport"', html)
        # 9 add fields (no notes; medication + supplements share one) + 1 edit field (no note edit)
        self.assertEqual(html.count('data-suggest="'), 9 + 1)
        self.assertIn("data-suggest-whole", html)
        self.assertIn('data-suggest-url="/food/suggestions/"', html)
        self.assertIn("js/food_suggest.js", html)


class FoodMedsTests(TestCase):
    """food-007: common medication + supplement input, classification dialog, move, dictionary page."""

    def setUp(self):
        _login_session(self.client)

    def _detail(self):
        return _detail_with(medication=[_entry("prestarium", category="medication", entry_id="m1")],
                            supplement=[_entry("zn", category="supplement", entry_id="s1")])

    def test_day_screen_has_one_meds_input_and_two_lists(self):
        fake, p = _patch_api({("GET", "/days/2026-10-20"): self._detail()})
        with p:
            html = self.client.get("/food/day/2026-10-20/").content.decode()
        self.assertIn('data-testid="add-meds"', html)
        self.assertNotIn('data-testid="add-medication"', html)
        self.assertNotIn('data-testid="add-supplement"', html)
        self.assertIn('hx-post="/food/day/2026-10-20/meds/"', html)
        positions = [html.index(f'data-testid="{t}"') for t in ("section-meds", "section-medication",
                                                                   "section-supplement", "add-meds")]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('data-testid="meds-dictionary-link"', html)
        self.assertIn('href="/food/settings/meds/"', html)
        self.assertEqual(html.count('data-testid="entry-move"'), 2)
        self.assertIn('"text_norm": "zn", "kind": "medication"', html)
        self.assertIn('"text_norm": "prestarium", "kind": "supplement"', html)
        self.assertNotIn('data-testid="classify-dialog"', html)
        self.assertIn("js/food_meds.js", html)

    def test_add_meds_known_items(self):
        fake, p = _patch_api({
            ("POST", "/days/2026-10-20/meds"): {"created": [], "needs_classification": []},
            ("GET", "/days/2026-10-20"): self._detail(),
        })
        with p:
            response = self.client.post("/food/day/2026-10-20/meds/", {"text": "zn, prestarium"})
        self.assertIn(("POST", "/days/2026-10-20/meds", {"text": "zn, prestarium"}), fake.calls)
        self.assertNotIn("X-Food-Error", response)
        self.assertNotIn("X-Food-Keep-Input", response)
        html = response.content.decode()
        self.assertIn('id="meds-lists"', html)
        self.assertEqual(html.count('data-testid="entry"'), 2)
        self.assertNotIn('data-testid="classify-dialog"', html)

    def test_add_meds_unknown_items_show_dialog(self):
        fake, p = _patch_api({
            ("POST", "/days/2026-10-20/meds"): {"created": [], "needs_classification": [
                {"text": "Emanera", "text_norm": "emanera"}, {"text": "zn", "text_norm": "zn"}]},
            ("GET", "/days/2026-10-20"): self._detail(),
        })
        with p:
            response = self.client.post("/food/day/2026-10-20/meds/", {"text": "Emanera, zn"})
        self.assertEqual(response["X-Food-Keep-Input"], "1")
        html = response.content.decode()
        self.assertIn('data-testid="classify-dialog"', html)
        self.assertEqual(html.count('data-testid="classify-item"'), 2)
        self.assertEqual(html.count('data-testid="classify-medication"'), 2)
        self.assertEqual(html.count('data-testid="classify-supplement"'), 2)
        self.assertIn('name="text" value="Emanera, zn"', html)
        self.assertIn('name="classify_norm" value="emanera"', html)

    def test_add_meds_sends_classification(self):
        fake, p = _patch_api({
            ("POST", "/days/2026-10-20/meds"): {"created": [], "needs_classification": []},
            ("GET", "/days/2026-10-20"): self._detail(),
        })
        with p:
            self.client.post("/food/day/2026-10-20/meds/", {
                "text": "Emanera, zn", "classify_norm": ["emanera", "zn", "x"],
                "classify_kind": ["medication", "supplement", "bogus"]})
        self.assertIn(("POST", "/days/2026-10-20/meds",
                       {"text": "Emanera, zn", "classify": {"emanera": "medication", "zn": "supplement"}}), fake.calls)

    def test_add_meds_error_keeps_text(self):
        fake, p = _patch_api({
            ("POST", "/days/2026-10-20/meds"): {"error": "empty_text", "status_code": 422},
            ("GET", "/days/2026-10-20"): self._detail(),
        })
        with p:
            response = self.client.post("/food/day/2026-10-20/meds/", {"text": " "})
        self.assertEqual(response["X-Food-Error"], "empty_text")
        self.assertEqual(response.content.decode().count('data-testid="entry-error"'), 1)

    def test_move_changes_dictionary_kind(self):
        fake, p = _patch_api({
            ("PUT", "/med-dictionary/vitamin%20d%2Fk"): {"text_norm": "vitamin d/k", "kind": "medication"},
            ("GET", "/days/2026-10-20"): self._detail(),
        })
        with p:
            response = self.client.post("/food/day/2026-10-20/meds/move/",
                                        {"text_norm": "vitamin d/k", "kind": "medication"})
        self.assertIn(("PUT", "/med-dictionary/vitamin%20d%2Fk", {"kind": "medication"}), fake.calls)
        self.assertNotIn("X-Food-Error", response)
        self.assertIn('id="meds-lists"', response.content.decode())

    def test_move_rejects_unknown_kind(self):
        fake, p = _patch_api({("GET", "/days/2026-10-20"): self._detail()})
        with p:
            response = self.client.post("/food/day/2026-10-20/meds/move/", {"text_norm": "zn", "kind": "food"})
        self.assertEqual(response["X-Food-Error"], "invalid_kind")
        self.assertNotIn("PUT", [c[0] for c in fake.calls])

    def test_dictionary_page(self):
        items = [{"text_norm": "prestarium", "display_text": "Prestarium", "kind": "medication", "usage_count": 3},
                 {"text_norm": "zn", "display_text": "zn", "kind": "supplement", "usage_count": 7}]
        fake, p = _patch_api({("GET", "/med-dictionary"): {"items": items}})
        with p:
            html = self.client.get("/food/settings/meds/").content.decode()
        self.assertIn('data-testid="meds-dictionary"', html)
        self.assertEqual(html.count('data-testid="dict-item"'), 2)
        self.assertIn("(7×)", html)
        start = html.index('data-text-norm="zn"')
        row = html[start:html.index("</li>", start)]
        marker = row.index('data-testid="dict-kind-supplement"')
        self.assertIn('aria-pressed="true"', row[row.rindex("<button", 0, marker):marker])
        self.assertIn('data-testid="nav-food-meds"', html)

    def test_dictionary_empty(self):
        fake, p = _patch_api({("GET", "/med-dictionary"): {"items": []}})
        with p:
            html = self.client.get("/food/settings/meds/").content.decode()
        self.assertIn('data-testid="dictionary-empty"', html)

    def test_dictionary_kind_and_delete(self):
        fake, p = _patch_api({
            ("PUT", "/med-dictionary/zn"): {"text_norm": "zn", "kind": "medication"},
            ("DELETE", "/med-dictionary/zn"): {},
            ("GET", "/med-dictionary"): {"items": []},
        })
        with p:
            response = self.client.post("/food/settings/meds/kind/", {"text_norm": "zn", "kind": "medication"})
            self.assertNotIn("X-Food-Error", response)
            response = self.client.post("/food/settings/meds/delete/", {"text_norm": "zn"})
            self.assertNotIn("X-Food-Error", response)
        self.assertIn(("PUT", "/med-dictionary/zn", {"kind": "medication"}), fake.calls)
        self.assertIn(("DELETE", "/med-dictionary/zn", None), fake.calls)
        self.assertIn('id="meds-dictionary"', response.content.decode())

    def test_anonymous(self):
        client = Client()
        self.assertRedirects(client.get("/food/settings/meds/"), reverse("login"), fetch_redirect_response=False)
        self.assertEqual(client.post("/food/day/2026-10-20/meds/", {"text": "zn"}).status_code, 401)
        self.assertEqual(client.post("/food/settings/meds/kind/", {"text_norm": "zn"}).status_code, 401)


def _cal_day(date, stool=None, gas=None, severity="none", entry_count=0):
    return {"date": date, "stool": stool, "gas": gas, "severity": severity, "entry_count": entry_count}


class FoodCalendarTests(TestCase):
    def setUp(self):
        _login_session(self.client)

    def _get(self, url, cal):
        fake, p = _patch_api({("GET", "/calendar"): cal})
        with p:
            response = self.client.get(url)
        return fake, response

    def test_february_grid(self):
        fake, response = self._get("/food/?month=2026-02", _calendar("2026-02"))
        html = response.content.decode()
        self.assertEqual(fake.params, [{"month": "2026-02"}])
        self.assertEqual(html.count('data-testid="cal-day"'), 28)
        self.assertIn('data-date="2026-02-28"', html)
        self.assertNotIn('data-date="2026-02-29"', html)
        # 1 February 2026 is a Sunday: six padding cells before it in a week starting on Monday.
        grid = html[html.index('data-testid="calendar"'):]
        self.assertEqual(grid[:grid.index('data-date="2026-02-01"')].count('data-testid="cal-pad"'), 6)
        self.assertIn('data-month="2026-02"', html)
        self.assertIn('href="?month=2026-01"', html)
        self.assertIn('href="?month=2026-03"', html)

    def test_dots_links_and_future_days(self):
        cal = _calendar("2026-10", [_cal_day("2026-10-05", 2, 9, "bad", 3), _cal_day("2026-10-06")])
        fake, response = self._get("/food/", cal)
        html = response.content.decode()
        self.assertEqual(fake.params, [None])
        self.assertIn('href="/food/day/2026-10-05/" data-testid="cal-day" data-date="2026-10-05"', html)
        self.assertIn('data-severity="bad" title="Stool 2, gas 9"', html)
        self.assertIn('data-severity="none" title="No stool / gas values"', html)
        self.assertEqual(html.count('data-testid="cal-dot"'), 2)
        # Missing past day and today: submit buttons creating the day; future day: no link.
        self.assertIn('name="date" value="2026-10-07"', html)
        self.assertIn('value="2026-10-24" class="cal-cell missing today"', html)
        self.assertIn('<span class="cal-cell future" data-testid="cal-day" data-date="2026-10-25">', html)
        self.assertIn('data-testid="cal-next" aria-disabled="true"', html)
        self.assertIn('data-testid="cal-legend"', html)

    def test_future_month_redirects_to_current(self):
        fake, response = self._get("/food/?month=2026-11", _calendar("2026-11"))
        self.assertRedirects(response, "/food/", fetch_redirect_response=False)

    def test_invalid_month_shows_current(self):
        fake, response = self._get("/food/?month=2026-13", _calendar("2026-10"))
        self.assertEqual(fake.params, [None])
        self.assertEqual(response.status_code, 200)

    def test_day_screen_links_back_to_its_month(self):
        fake, p = _patch_api({("GET", "/days/2026-09-20"): _day_detail("2026-09-20")})
        with p:
            html = self.client.get("/food/day/2026-09-20/").content.decode()
        self.assertIn('href="/food/?month=2026-09" data-testid="back-to-calendar"', html)


class FoodListTests(TestCase):
    def setUp(self):
        _login_session(self.client)

    def _summary(self, date, **kw):
        return {"date": date, "stool": None, "gas": None, "severity": "none", "sleep_quality": None,
                "weights": [], "bp": [], "food_preview": [], "entry_count": 0, **kw}

    def test_row_contains_preview_and_digestion(self):
        days = [self._summary("2026-10-20", stool=4, gas=6, severity="mid", sleep_quality=3, weights=[80.6],
                              bp=["130/85 72"], food_preview=["toasty", "kafe"])]
        fake, p = _patch_api({("GET", "/days"): {"schema_version": "1.0", "page": 1, "page_size": 30,
                                                 "total": 1, "days": days}})
        with p:
            html = self.client.get("/food/list/").content.decode()
        self.assertEqual(fake.params, [{"page": 1, "page_size": 30}])
        self.assertIn('href="/food/day/2026-10-20/" data-testid="list-day"', html)
        self.assertIn('title="Stool / gas">4/6</span>', html)
        self.assertIn("toasty, kafe", html)
        self.assertIn("80.6 kg", html)
        self.assertIn("130/85 72", html)
        self.assertIn('data-severity="mid"', html)
        self.assertNotIn('data-testid="list-next-page"', html)

    def test_pagination_links(self):
        days = [self._summary(f"2026-09-{n:02d}") for n in range(1, 6)]
        fake, p = _patch_api({("GET", "/days"): {"schema_version": "1.0", "page": 2, "page_size": 30,
                                                 "total": 65, "days": days}})
        with p:
            html = self.client.get("/food/list/?page=2").content.decode()
        self.assertEqual(fake.params, [{"page": 2, "page_size": 30}])
        self.assertIn('href="?page=1" data-testid="list-prev-page"', html)
        self.assertIn('href="?page=3" data-testid="list-next-page"', html)
        self.assertIn("2 / 3", html)
