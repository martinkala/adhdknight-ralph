"""food-010: translations (.po / .mo), language of the session and the cookie, language switch."""
import ast
import gettext
from datetime import date
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from food.templatetags.food_format import food_date, number
from food.tests.test_views import _day_detail, _patch_api

LOCALE_DIR = settings.BASE_DIR / "locale"
LANGUAGE_CODES = [code for code, _ in settings.LANGUAGES]


def _parse_po(path):
    """Minimal .po reader: list of {"id", "plural", "strings", "fuzzy"}; the header entry included."""
    entries, current, field = [], None, None

    def start():
        entry = {"id": "", "plural": None, "strings": {}, "fuzzy": False, "flags": ""}
        entries.append(entry)
        return entry

    flags = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("#,"):
            flags = line
        elif line.startswith("#") or not line:
            continue
        elif line.startswith("msgctxt") or (line.startswith("msgid ") and (current is None or field != "ctxt")):
            current = start()
            current["fuzzy"] = "fuzzy" in flags
            flags = ""
            if line.startswith("msgctxt"):
                field = "ctxt"
                continue
            field, current["id"] = "id", ast.literal_eval(line[6:])
        elif line.startswith("msgid "):
            field, current["id"] = "id", ast.literal_eval(line[6:])
        elif line.startswith("msgid_plural"):
            field, current["plural"] = "plural", ast.literal_eval(line[13:])
        elif line.startswith("msgstr["):
            index = int(line[7:line.index("]")])
            field = ("str", index)
            current["strings"][index] = ast.literal_eval(line[line.index("]") + 2:])
        elif line.startswith("msgstr"):
            field = ("str", 0)
            current["strings"][0] = ast.literal_eval(line[7:])
        elif line.startswith('"'):
            value = ast.literal_eval(line)
            if field == "id":
                current["id"] += value
            elif field == "plural":
                current["plural"] += value
            elif isinstance(field, tuple):
                current["strings"][field[1]] += value
    return entries


def _po_path(language):
    return LOCALE_DIR / language / "LC_MESSAGES" / "django.po"


class TranslationFilesTests(TestCase):
    def test_po_and_mo_exist_for_all_languages(self):
        for language in LANGUAGE_CODES:
            with self.subTest(language=language):
                self.assertTrue(_po_path(language).is_file())
                self.assertTrue(_po_path(language).with_suffix(".mo").is_file())

    def test_sk_and_cs_have_no_empty_or_fuzzy_messages(self):
        for language in ("sk", "cs"):
            entries = [e for e in _parse_po(_po_path(language)) if e["id"]]
            self.assertGreater(len(entries), 100)
            for entry in entries:
                with self.subTest(language=language, msgid=entry["id"]):
                    self.assertFalse(entry["fuzzy"])
                    self.assertTrue(entry["strings"])
                    self.assertTrue(all(entry["strings"].values()))

    def test_mo_files_are_compiled_from_current_po(self):
        for language in LANGUAGE_CODES:
            with _po_path(language).with_suffix(".mo").open("rb") as f:
                catalog = gettext.GNUTranslations(f)._catalog
            for entry in _parse_po(_po_path(language)):
                if not entry["id"] or not all(entry["strings"].values()):
                    continue
                with self.subTest(language=language, msgid=entry["id"]):
                    if entry["plural"] is None:
                        self.assertEqual(catalog.get(entry["id"]), entry["strings"][0])
                    else:
                        for index, value in entry["strings"].items():
                            self.assertEqual(catalog.get((entry["id"], index)), value)

    def test_placeholders_are_kept_in_translations(self):
        import re
        placeholder = re.compile(r"%\(\w+\)s|<\w+>|</\w+>")
        for language in ("sk", "cs"):
            for entry in _parse_po(_po_path(language)):
                if entry["id"]:
                    with self.subTest(language=language, msgid=entry["id"]):
                        self.assertEqual(sorted(placeholder.findall(entry["id"])),
                                         sorted(placeholder.findall(entry["strings"][0])))


def _login_session(client, language=None):
    session = client.session
    session["user_email"] = "user@example.com"
    session["token"] = "fake-token"
    if language:
        session["language"] = language
    session.save()


DAY_LABELS = {"sk": ("Raňajky", "Večera"), "cs": ("Snídaně", "Večeře"), "en": ("Breakfast", "Dinner")}


class SessionLanguageTests(TestCase):
    def _day(self):
        fake, p = _patch_api({("GET", "/days/2026-10-20"): _day_detail()})
        with p:
            return self.client.get("/food/day/2026-10-20/")

    def test_html_lang_follows_session_language(self):
        _login_session(self.client, "cs")
        self.assertContains(self._day(), '<html lang="cs">')

    def test_default_language_is_sk(self):
        _login_session(self.client)
        response = self._day()
        self.assertContains(response, '<html lang="sk">')
        self.assertContains(response, "Raňajky")

    def test_day_screen_in_each_language(self):
        for language, labels in DAY_LABELS.items():
            with self.subTest(language=language):
                _login_session(self.client, language)
                response = self._day()
                for label in labels:
                    self.assertContains(response, label)

    def test_day_screen_date_format(self):
        expected = {"sk": "20. 10. 2026", "cs": "20. 10. 2026", "en": "20 Oct 2026"}
        weekday = {"sk": "utorok", "cs": "úterý", "en": "Tuesday"}
        for language in LANGUAGE_CODES:
            with self.subTest(language=language):
                _login_session(self.client, language)
                html = self._day().content.decode()
                self.assertIn(f"<span>{expected[language]}</span>", html)
                self.assertIn(weekday[language], html.lower() if language != "en" else html)

    def test_day_exists_error_in_session_language(self):
        messages = {"sk": "Deň už existuje", "cs": "Den již existuje", "en": "Day already exists"}
        for language, message in messages.items():
            with self.subTest(language=language):
                _login_session(self.client, language)
                fake, p = _patch_api({
                    ("POST", "/days"): {"error": "day_exists", "status_code": 409},
                    ("GET", "/calendar"): {"schema_version": "1.0", "month": "2026-10", "today": "2026-10-24",
                                           "days": []},
                })
                with p:
                    response = self.client.post("/food/days/new/", {"date": "2026-10-20"})
                self.assertContains(response, message)

    def test_calendar_month_and_weekdays_are_translated(self):
        month = {"sk": "október 2026", "cs": "říjen 2026", "en": "October 2026"}
        monday = {"sk": "po", "cs": "po", "en": "Mon"}
        for language in LANGUAGE_CODES:
            with self.subTest(language=language):
                _login_session(self.client, language)
                fake, p = _patch_api({("GET", "/calendar"): {"schema_version": "1.0", "month": "2026-10",
                                                             "today": "2026-10-24", "days": []}})
                with p:
                    html = self.client.get("/food/").content.decode()
                self.assertIn(month[language], html.lower() if language != "en" else html)
                self.assertIn(f'<span class="cal-weekday">{monday[language]}</span>', html)

    def test_anonymous_uses_cookie_language(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        response = self.client.get(reverse("login"))
        self.assertContains(response, '<html lang="en">')
        self.assertContains(response, "Log in")

    def test_anonymous_without_cookie_is_sk(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, '<html lang="sk">')
        self.assertContains(response, 'data-testid="lang-switch"')

    def test_unsupported_cookie_falls_back_to_sk(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "de"
        self.assertContains(self.client.get(reverse("login")), '<html lang="sk">')

    def test_session_language_wins_over_cookie(self):
        _login_session(self.client, "cs")
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        self.assertContains(self._day(), '<html lang="cs">')

    def test_login_page_switch_sets_cookie_only(self):
        response = self.client.post(reverse("set_language"), {"language": "cs", "next": "/login/"})
        self.assertRedirects(response, "/login/", fetch_redirect_response=False)
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "cs")
        self.assertContains(self.client.get(reverse("login")), "Přihlásit se")


def _response(status_code, json=None):
    import httpx
    return httpx.Response(status_code, json=json, request=httpx.Request("GET", "http://api.test"))


class ChangeLanguageTests(TestCase):
    def test_account_page_has_language_select(self):
        _login_session(self.client, "cs")
        me = {"email": "user@example.com", "created_at": "2026-10-01T00:00:00Z", "total_days": 0}
        with patch("core.api_client.get_me", return_value=me):
            response = self.client.get(reverse("account"))
        self.assertContains(response, 'data-testid="language-select"')
        self.assertContains(response, '<option value="cs" lang="cs" selected>')

    def test_change_language_patches_api_and_updates_session_and_cookie(self):
        _login_session(self.client, "sk")
        with patch("core.api_client.httpx.request", return_value=_response(200, {
                "schema_version": "1.0", "language": "en", "timezone": "Europe/Bratislava"})) as request:
            response = self.client.post(reverse("change_language"), {"language": "en"})
        self.assertRedirects(response, reverse("account"), fetch_redirect_response=False)
        self.assertEqual(request.call_args.args[:2][0], "PATCH")
        self.assertTrue(request.call_args.args[1].endswith("/api/v1/user/settings"))
        self.assertEqual(request.call_args.kwargs["json"], {"language": "en"})
        self.assertEqual(self.client.session["language"], "en")
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "en")

    def test_invalid_language_is_rejected_without_api_call(self):
        _login_session(self.client, "sk")
        with patch("core.api_client.httpx.request") as request:
            self.client.post(reverse("change_language"), {"language": "de"})
        request.assert_not_called()
        self.assertEqual(self.client.session["language"], "sk")

    def test_api_error_keeps_language(self):
        _login_session(self.client, "sk")
        with patch("core.api_client.httpx.request", side_effect=__import__("httpx").ConnectError("down")):
            self.client.post(reverse("change_language"), {"language": "en"})
        self.assertEqual(self.client.session["language"], "sk")

    def test_change_language_requires_login(self):
        response = self.client.post(reverse("change_language"), {"language": "en"})
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    def test_login_loads_language_and_sets_cookie(self):
        tokens = {"access_token": "a", "refresh_token": "r", "token_type": "bearer", "expires_in": 900}
        with patch("core.api_client.post_login", return_value=tokens), \
                patch("core.api_client.get_user_settings", return_value={"language": "cs"}):
            response = self.client.post(reverse("login"), {"email": "user@example.com", "password": "x" * 8})
        self.assertEqual(self.client.session["language"], "cs")
        self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, "cs")

    def test_login_error_is_translated(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        with patch("core.api_client.post_login", return_value={"error": "Invalid credentials"}):
            response = self.client.post(reverse("login"), {"email": "user@example.com", "password": "x" * 8})
        self.assertContains(response, "Wrong e-mail or password.")


class FormatTests(TestCase):
    def test_date_and_decimal_by_language(self):
        day = date(2026, 10, 24)
        cases = {"sk": ("24. 10. 2026", "0,5"), "cs": ("24. 10. 2026", "0,5"), "en": ("24 Oct 2026", "0.5")}
        for language, (formatted_date, formatted_number) in cases.items():
            with self.subTest(language=language), translation.override(language):
                self.assertEqual(food_date(day), formatted_date)
                self.assertEqual(number(0.5), formatted_number)
