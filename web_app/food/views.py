from datetime import date as date_type

from django.contrib import messages
from django.http import Http404, HttpResponse, QueryDict
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _, gettext_lazy
from django.views.decorators.http import require_http_methods, require_POST

from core.views import _require_login
from food import api_client

# Sections of the day screen in display order (food-004 FR-3). Entry categories follow constitution D2.
ENTRY_SECTION_LABELS = {
    "breakfast": gettext_lazy("Breakfast"),
    "morning_snack": gettext_lazy("Morning snack"),
    "lunch": gettext_lazy("Lunch"),
    "afternoon_snack": gettext_lazy("Afternoon snack"),
    "dinner": gettext_lazy("Dinner"),
    "after_dinner": gettext_lazy("After dinner"),
    "unassigned": gettext_lazy("Unassigned / during the day"),
    "medication": gettext_lazy("Medication"),
    "supplement": gettext_lazy("Supplements"),
    "sport": gettext_lazy("Sport"),
    "note": gettext_lazy("Notes"),
}
SECTION_ORDER = (
    "breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner", "after_dinner", "unassigned",
    "medication", "supplement", "bp", "weight", "values", "sport", "note",
)
SLEEP_CHOICES = ((1, gettext_lazy("Bad")), (2, gettext_lazy("Average")), (3, gettext_lazy("OK")))
DIGESTION_CHOICES = tuple(range(1, 11))
DAY_VALUE_FIELDS = ("sleep_quality", "stool", "gas")

_ERRORS = {
    "server_unavailable": gettext_lazy("Server is not available. Try again later."),
    "server_error": gettext_lazy("Loading data failed. Try again."),
    "invalid_input": gettext_lazy("Enter a valid date."),
    "day_exists": gettext_lazy("Day already exists"),
    "future_date": gettext_lazy("A day in the future cannot be added."),
}


def _error_message(code: str) -> str:
    return str(_ERRORS.get(code, _ERRORS["server_error"]))


def _parse_date(value: str) -> date_type | None:
    try:
        return date_type.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _today(request) -> str | None:
    return api_client.call(request, "GET", "/today").get("date")


def _render_home(request, error: str | None = None, existing_date: str | None = None, status: int = 200):
    today = _today(request)
    context = {
        "today": today,
        "error": error,
        "error_message": _error_message(error) if error else None,
        "existing_date": existing_date,
    }
    return render(request, "food/home.html", context, status=status)


def home(request):
    if not _require_login(request):
        return redirect("login")
    return _render_home(request)


@require_POST
def open_today(request):
    """Opens today's day, creating it first if it does not exist yet (one tap)."""
    if not _require_login(request):
        return redirect("login")
    today = api_client.call(request, "GET", "/today")
    if "error" in today:
        return _render_home(request, error=today["error"])
    if not today["exists"]:
        created = api_client.call(request, "POST", "/days", json={"date": today["date"]})
        if "error" in created and created["error"] != "day_exists":
            return _render_home(request, error=created["error"])
    return redirect("food:day", day=today["date"])


@require_POST
def new_day(request):
    if not _require_login(request):
        return redirect("login")
    day = request.POST.get("date", "").strip()
    if _parse_date(day) is None:
        return _render_home(request, error="invalid_input")
    result = api_client.call(request, "POST", "/days", json={"date": day})
    if "error" in result:
        existing = day if result["error"] == "day_exists" else None
        return _render_home(request, error=result["error"], existing_date=existing)
    return redirect("food:day", day=day)


def _values_context(day: dict, save_status: str | None = None) -> dict:
    return {
        "day": day,
        "sleep_choices": SLEEP_CHOICES,
        "digestion_choices": DIGESTION_CHOICES,
        "save_status": save_status,
    }


def day_view(request, day):
    if not _require_login(request):
        return redirect("login")
    detail = api_client.call(request, "GET", f"/days/{day}")
    if detail.get("status_code") in (404, 422):
        return _render_missing_day(request, day)
    if "error" in detail:
        return render(request, "food/day_error.html", {"error_message": _error_message(detail["error"])}, status=502)

    sections = []
    for key in SECTION_ORDER:
        if key in ENTRY_SECTION_LABELS:
            sections.append({"kind": "entries", "key": key, "label": ENTRY_SECTION_LABELS[key],
                             "items": detail["entries"].get(key, [])})
        else:
            sections.append({"kind": key, "key": key})
    context = {
        **_values_context(detail),
        "day_date": _parse_date(day),
        "sections": sections,
    }
    return render(request, "food/day.html", context)


def _render_missing_day(request, day: str):
    parsed = _parse_date(day)
    today = _today(request)
    can_create = parsed is not None and today is not None and day <= today
    return render(request, "food/day_missing.html", {"day": day, "day_date": parsed, "can_create": can_create},
                  status=404)


def _parse_value(raw: str | None) -> int | None:
    raw = (raw or "").strip()
    return int(raw) if raw.isdigit() else None


@require_http_methods(["PATCH"])
def day_values(request, day):
    """HTMX autosave of one or more day values; an empty value clears it. Returns the values partial."""
    if not _require_login(request):
        return HttpResponse(status=401)
    data = QueryDict(request.body)
    payload = {field: _parse_value(data.get(field)) for field in DAY_VALUE_FIELDS if field in data}
    result = api_client.call(request, "PATCH", f"/days/{day}", json=payload)
    if "error" not in result:
        return render(request, "food/_day_values.html", _values_context(result, "saved"))
    current = api_client.call(request, "GET", f"/days/{day}")
    if "error" in current:
        raise Http404
    return render(request, "food/_day_values.html", _values_context(current, "error"))


@require_POST
def delete_day(request, day):
    """Second confirmation is checked here too: the typed date must match the day exactly."""
    if not _require_login(request):
        return redirect("login")
    if request.POST.get("confirm_date", "").strip() != day:
        messages.error(request, _("The day was not deleted: the date does not match."))
        return redirect("food:day", day=day)
    result = api_client.call(request, "DELETE", f"/days/{day}")
    if "error" in result:
        messages.error(request, _error_message(result["error"]))
        return redirect("food:day", day=day)
    messages.success(request, _("The day was deleted."))
    return redirect("food:home")
