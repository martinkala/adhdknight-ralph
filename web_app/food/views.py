from datetime import date as date_type
from urllib.parse import quote

from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse, QueryDict
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
    "day_not_found": gettext_lazy("The day does not exist anymore."),
    "entry_not_found": gettext_lazy("The entry does not exist anymore."),
    "measurement_not_found": gettext_lazy("The measurement does not exist anymore."),
    "empty_text": gettext_lazy("Enter a text."),
    "text_too_long": gettext_lazy("The text is too long (max. 200 characters)."),
    "invalid_quantity": gettext_lazy("Enter a valid quantity."),
    "invalid_unit": gettext_lazy("Enter a valid quantity."),
    "unit_without_quantity": gettext_lazy("Enter a valid quantity."),
    "bp_format": gettext_lazy("Enter blood pressure as 130/85, optionally with pulse and time: 130/85 72 7:30."),
    "bp_range": gettext_lazy("Blood pressure is out of range (systolic 60–260, diastolic 30–160, pulse 30–220)."),
    "weight_range": gettext_lazy("Enter weight between 20 and 300 kg."),
    "time_format": gettext_lazy("Enter time as HH:MM."),
    "invalid_kind": gettext_lazy("Choose medication or supplement."),
    "dictionary_item_not_found": gettext_lazy("The item is not in the dictionary anymore."),
}
UNIT_CHOICES = ("ks", "l", "ml", "g", "kg")
# Autocomplete group per entry category (constitution D2); notes have none.
SUGGESTION_GROUPS = {
    **{c: "food" for c in ("breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner", "after_dinner",
                           "unassigned")},
    "medication": "meds",
    "supplement": "meds",
    "sport": "sport",
}
SUGGESTIONS_LIMIT_MAX = 20
MED_KINDS = ("medication", "supplement")
MED_KIND_LABELS = (("medication", gettext_lazy("Medication")), ("supplement", gettext_lazy("Supplement")))


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
        if key in MED_KINDS:
            # Medication and supplements share one input (food-007 FR-3), the lists stay separate.
            if key == MED_KINDS[0]:
                sections.append({"kind": "meds", "key": "meds", **_meds_context(detail)})
        elif key in ENTRY_SECTION_LABELS:
            sections.append(_entry_section(detail, key))
        else:
            sections.append({"kind": key, "key": key})
    context = {
        **_values_context(detail),
        "day_date": _parse_date(day),
        "sections": sections,
        "unit_choices": UNIT_CHOICES,
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


# --- Entries and measurements (food-005) -----------------------------------------------------
# HTMX endpoints return the re-rendered list partial of the section. A failed save returns the
# current list with an error message and the `X-Food-Error` header, so the input keeps its text.


def _entry_section(detail: dict, key: str) -> dict:
    return {"kind": "entries", "key": key, "label": ENTRY_SECTION_LABELS[key],
            "group": SUGGESTION_GROUPS.get(key), "items": detail["entries"].get(key, [])}


def _decimal_or_none(raw: str | None):
    """"0,5" -> 0.5; empty -> None; raises ValueError for anything else."""
    raw = (raw or "").strip().replace(",", ".")
    return float(raw) if raw else None


def _partial(request, day: str, template: str, context_for, error: str | None = None):
    detail = api_client.call(request, "GET", f"/days/{day}")
    if "error" in detail:
        error = error or detail["error"]
        response = HttpResponse(_error_message(error))
        response["X-Food-Error"] = error
        return response
    context = {"day": detail, "unit_choices": UNIT_CHOICES, "error": error,
               "error_message": _error_message(error) if error else None, **context_for(detail)}
    response = render(request, template, context)
    if error:
        response["X-Food-Error"] = error
    return response


def _entries_partial(request, day: str, category: str, error: str | None = None):
    return _partial(request, day, "food/_entries.html", lambda d: {"section": _entry_section(d, category)}, error)


def _check_category(category: str):
    if category not in ENTRY_SECTION_LABELS:
        raise Http404


@require_POST
def add_entries(request, day, category):
    if not _require_login(request):
        return HttpResponse(status=401)
    _check_category(category)
    result = api_client.call(request, "POST", f"/days/{day}/entries",
                             json={"category": category, "text": request.POST.get("text", "")})
    return _entries_partial(request, day, category, result.get("error"))


def _entry_changes(data: QueryDict) -> dict:
    changes = {}
    if "text" in data:
        changes["text"] = data["text"]
    if "quantity" in data:
        changes["quantity"] = _decimal_or_none(data["quantity"])
        changes["unit"] = data.get("unit") or None
    if "intensity" in data:
        changes["intensity"] = _parse_value(data["intensity"])
    return changes


@require_http_methods(["PATCH", "DELETE"])
def entry(request, day, category, entry_id):
    """PATCH saves inline edits (text, quantity, intensity); DELETE removes the entry (one tap)."""
    if not _require_login(request):
        return HttpResponse(status=401)
    _check_category(category)
    if request.method == "DELETE":
        result = api_client.call(request, "DELETE", f"/entries/{entry_id}")
        return _entries_partial(request, day, category, result.get("error"))
    try:
        changes = _entry_changes(QueryDict(request.body))
    except ValueError:
        return _entries_partial(request, day, category, "invalid_quantity")
    result = api_client.call(request, "PATCH", f"/entries/{entry_id}", json=changes)
    return _entries_partial(request, day, category, result.get("error"))


def entry_quantities(request, day, category, entry_id):
    """Quantity popover: the most used quantities of the entry text + manual entry."""
    if not _require_login(request):
        return HttpResponse(status=401)
    _check_category(category)
    result = api_client.call(request, "GET", "/quantities",
                             params={"text": request.GET.get("text", ""), "category": category})
    context = {"day": {"date": day}, "section": {"key": category}, "entry_id": entry_id,
               "options": result.get("options", []), "unit_choices": UNIT_CHOICES}
    return render(request, "food/_qty_popover.html", context)


def suggestions(request):
    """Autocomplete JSON for food_suggest.js (food-006). Errors give an empty list, typing goes on."""
    if not _require_login(request):
        return HttpResponse(status=401)
    group = request.GET.get("group", "")
    if group not in SUGGESTION_GROUPS.values():
        return JsonResponse({"suggestions": []})
    try:
        limit = min(max(int(request.GET.get("limit", 10)), 1), SUGGESTIONS_LIMIT_MAX)
    except ValueError:
        limit = 10
    result = api_client.call(request, "GET", "/suggestions",
                             params={"group": group, "q": request.GET.get("q", "")[:200], "limit": limit})
    return JsonResponse({"suggestions": result.get("suggestions", [])})


# --- Medication and supplements (food-007) ---------------------------------------------------


def _meds_context(detail: dict, classify_items=None, meds_text: str = "") -> dict:
    return {"meds_sections": [_entry_section(detail, kind) for kind in MED_KINDS],
            "classify_items": classify_items or [], "meds_text": meds_text}


def _meds_partial(request, day: str, error: str | None = None, classify_items=None, meds_text: str = ""):
    response = _partial(request, day, "food/_meds.html",
                        lambda d: _meds_context(d, classify_items, meds_text), error)
    if classify_items and "X-Food-Error" not in response:
        # Keeps the typed text in the quick add field while the classification dialog is open.
        response["X-Food-Keep-Input"] = "1"
    return response


@require_POST
def add_meds(request, day):
    """The common medication + supplement input. Unknown items come back from the API in
    `needs_classification`; the partial then contains the "medication or supplement?" dialog."""
    if not _require_login(request):
        return HttpResponse(status=401)
    text = request.POST.get("text", "")
    classify = {norm: kind for norm, kind in zip(request.POST.getlist("classify_norm"),
                                                 request.POST.getlist("classify_kind")) if kind in MED_KINDS}
    payload = {"text": text, "classify": classify} if classify else {"text": text}
    result = api_client.call(request, "POST", f"/days/{day}/meds", json=payload)
    if result.get("needs_classification"):
        return _meds_partial(request, day, classify_items=result["needs_classification"], meds_text=text)
    return _meds_partial(request, day, result.get("error"))


def _put_med_kind(request, text_norm: str, kind: str) -> dict:
    if kind not in MED_KINDS or not text_norm:
        return {"error": "invalid_kind"}
    return api_client.call(request, "PUT", f"/med-dictionary/{quote(text_norm, safe='')}", json={"kind": kind})


@require_POST
def move_med(request, day):
    """Moves an entry (and every entry of its text) to the other section by changing the dictionary."""
    if not _require_login(request):
        return HttpResponse(status=401)
    result = _put_med_kind(request, request.POST.get("text_norm", ""), request.POST.get("kind", ""))
    return _meds_partial(request, day, result.get("error"))


def _render_dictionary(request, template: str, error: str | None = None, status: int = 200):
    result = api_client.call(request, "GET", "/med-dictionary")
    error = error or result.get("error")
    context = {"items": result.get("items", []), "kinds": MED_KIND_LABELS, "error": error,
               "error_message": _error_message(error) if error else None}
    response = render(request, template, context, status=status)
    if error:
        response["X-Food-Error"] = error
    return response


def meds_dictionary(request):
    if not _require_login(request):
        return redirect("login")
    return _render_dictionary(request, "food/meds_dictionary.html")


@require_POST
def meds_dictionary_kind(request):
    if not _require_login(request):
        return HttpResponse(status=401)
    result = _put_med_kind(request, request.POST.get("text_norm", ""), request.POST.get("kind", ""))
    return _render_dictionary(request, "food/_meds_dictionary.html", result.get("error"))


@require_POST
def meds_dictionary_delete(request):
    if not _require_login(request):
        return HttpResponse(status=401)
    text_norm = request.POST.get("text_norm", "")
    result = api_client.call(request, "DELETE", f"/med-dictionary/{quote(text_norm, safe='')}") if text_norm \
        else {"error": "dictionary_item_not_found"}
    return _render_dictionary(request, "food/_meds_dictionary.html", result.get("error"))


def _measurements_partial(request, day: str, kind: str, error: str | None = None):
    return _partial(request, day, f"food/_{kind}.html", lambda d: {}, error)


@require_POST
def add_blood_pressure(request, day):
    if not _require_login(request):
        return HttpResponse(status=401)
    # Without a time on today's day, the server fills in the current local time.
    result = api_client.call(request, "POST", f"/days/{day}/blood-pressures",
                             json={"raw": request.POST.get("raw", ""), "fill_time": True})
    return _measurements_partial(request, day, "bp", result.get("error"))


@require_http_methods(["PATCH", "DELETE"])
def blood_pressure(request, day, record_id):
    if not _require_login(request):
        return HttpResponse(status=401)
    if request.method == "DELETE":
        result = api_client.call(request, "DELETE", f"/blood-pressures/{record_id}")
    else:
        data = QueryDict(request.body)
        result = api_client.call(request, "PATCH", f"/blood-pressures/{record_id}",
                                 json={"raw": data.get("raw", ""), "note": data.get("note", "")})
    return _measurements_partial(request, day, "bp", result.get("error"))


def _weight_payload(data) -> dict:
    kg = _decimal_or_none(data.get("kg"))
    if kg is None:
        raise ValueError("kg")
    return {"kg": kg, "measured_at": data.get("measured_at") or None, "note": data.get("note", "")}


@require_POST
def add_weight(request, day):
    if not _require_login(request):
        return HttpResponse(status=401)
    try:
        payload = _weight_payload(request.POST)
    except ValueError:
        return _measurements_partial(request, day, "weight", "weight_range")
    result = api_client.call(request, "POST", f"/days/{day}/weights", json=payload)
    return _measurements_partial(request, day, "weight", result.get("error"))


@require_http_methods(["PATCH", "DELETE"])
def weight(request, day, record_id):
    if not _require_login(request):
        return HttpResponse(status=401)
    if request.method == "DELETE":
        result = api_client.call(request, "DELETE", f"/weights/{record_id}")
        return _measurements_partial(request, day, "weight", result.get("error"))
    try:
        payload = _weight_payload(QueryDict(request.body))
    except ValueError:
        return _measurements_partial(request, day, "weight", "weight_range")
    result = api_client.call(request, "PATCH", f"/weights/{record_id}", json=payload)
    return _measurements_partial(request, day, "weight", result.get("error"))
