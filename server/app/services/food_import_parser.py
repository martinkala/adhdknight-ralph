"""Parser of pasted import text (food-011 FR-1): TSV / CSV in format C of the Google Sheets diary
(`docs/food/import-mapping.md`, section 4) and JSON in the export format (`FoodExport`, food-009).

A pure function without database access: medication and supplement items of TSV / CSV are left
unclassified (`ParsedDay.meds`), the merge sorts them by the user's dictionary. Typos are never
corrected (constitution D8). Invalid values are reported in `issues`, never dropped silently."""
import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date as date_type
from decimal import Decimal, InvalidOperation

from pydantic import ValidationError

from app.schemas.food import FoodExport
from app.services.food_constants import (
    ALL_CATEGORIES, CATEGORY_GROUP, DIGESTION_MAX, DIGESTION_MIN, INTENSITY_MAX, INTENSITY_MIN,
    SLEEP_QUALITY_MAX, SLEEP_QUALITY_MIN, SPORT_CATEGORIES, TEXT_MAX_LENGTH, UNITS,
)
from app.services.food_days import DAY_VALUE_FIELDS, FoodDayError
from app.services.food_measurements import (
    MeasurementError, normalize_time, parse_blood_pressure, validate_blood_pressure, validate_weight,
)
from app.services.food_quantity import ParsedItem, merge_duplicates, parse_item
from app.services.food_text import clean_text, normalize, split_entries

FORMATS = ("auto", "tsv", "csv", "json")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DIGESTION = re.compile(r"^(\d{1,2})\s*[/,]\s*(\d{1,2})$")
_PRECISION = Decimal("0.001")

# Format C columns by normalized header name (trim, lower case, no diacritics).
_COLUMNS = {
    "spanok": "sleep_quality",
    "ranajky": "breakfast",
    "desiata": "morning_snack",
    "obed": "lunch",
    "olovrant": "afternoon_snack",
    "vecera": "dinner",
    "post vecera": "after_dinner",
    "oills": "meds",
    "pils": "meds",
    "pills": "meds",
    "medical note": "note",
    "note": "note",
    "presure": "blood_pressure",
    "dig problemy (1-10) s/v": "digestion",
    "w": "weight",
    "sport": "sport",
}
_SYMPTOMS = re.compile(r"^symptoms(?: \d+)?$")  # "symptoms 12", "symptoms 1", "symptoms 2"
_IGNORED_COLUMNS = {"", "pohyb"}
# Headers of the old formats A (2022–2024) and B (2025); those are imported by the LLM outside the app.
_LEGACY_COLUMNS = {"wlk", "pos", "str", "end", "problemy (1-10) s/v"}
# Column order of 2026.csv, used when the pasted text starts with a day row instead of the header.
DEFAULT_HEADER = (
    "", "pohyb", "spanok", "Ranajky", "desiata", "obed", "olovrant", "vecera", "post vecera", "oills",
    "medical note", "presure", "dig problemy (1-10) s/v", "symptoms 12", "symptoms 2", "w", "sport", "note",
)


class ImportFormatError(FoodDayError):
    """The whole input cannot be read (unsupported_format_legacy, invalid_json, missing_header, ...)."""


@dataclass
class ImportItem:
    text: str
    quantity: Decimal | None = None
    unit: str | None = None
    intensity: int | None = None


@dataclass
class ParsedDay:
    date: str
    values: dict[str, int] = field(default_factory=dict)
    entries: dict[str, list[ImportItem]] = field(default_factory=dict)
    # TSV / CSV medication + supplement items, sorted later by the user's dictionary.
    meds: list[ImportItem] = field(default_factory=list)
    weights: list[dict] = field(default_factory=list)  # {kg: Decimal, measured_at, note}
    blood_pressures: list[dict] = field(default_factory=list)  # {systolic, diastolic, pulse, measured_at, note}

    def is_empty(self) -> bool:
        return not (self.values or any(self.entries.values()) or self.meds or self.weights or self.blood_pressures)


@dataclass
class ParsedImport:
    format: str
    days: list[ParsedDay] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)  # {date, column, value, code}
    skipped_empty_days: list[str] = field(default_factory=list)
    unknown_columns: list[str] = field(default_factory=list)


def detect_format(raw_text: str) -> str:
    """JSON if the text starts with "{", TSV if the first line contains a TAB, otherwise CSV."""
    text = raw_text.lstrip("﻿ \t\r\n")
    if text.startswith("{"):
        return "json"
    first_line = raw_text.lstrip("﻿\r\n").split("\n", 1)[0]
    return "tsv" if "\t" in first_line else "csv"


def parse_import(raw_text: str, fmt: str, today: str) -> ParsedImport:
    """Parses the input; days after `today` (YYYY-MM-DD, the user's today) are reported, not imported."""
    if fmt not in FORMATS:
        raise ImportFormatError("invalid_format")
    if not raw_text.strip():
        raise ImportFormatError("empty_input")
    if fmt == "auto":
        fmt = detect_format(raw_text)
    result = ParsedImport(format=fmt)
    if fmt == "json":
        days = _parse_json(raw_text, result)
    else:
        days = _parse_table(raw_text, "\t" if fmt == "tsv" else ",", result)

    by_date: dict[str, ParsedDay] = {}
    for day in days:
        if day.date > today:
            _issue(result, day.date, None, day.date, "future_date")
        elif day.is_empty() and fmt != "json":
            result.skipped_empty_days.append(day.date)
        elif day.date in by_date:
            _combine(by_date[day.date], day, result)
        else:
            by_date[day.date] = day
    result.days = sorted(by_date.values(), key=lambda d: d.date)
    return result


def _issue(result: ParsedImport, date: str | None, column: str | None, value, code: str) -> None:
    result.issues.append({"date": date, "column": column, "value": "" if value is None else str(value), "code": code})


def _combine(target: ParsedDay, day: ParsedDay, result: ParsedImport) -> None:
    """The same date twice in one input: lists are joined, a different day value is reported."""
    for name, value in day.values.items():
        if name in target.values and target.values[name] != value:
            _issue(result, day.date, name, value, "duplicate_value")
        else:
            target.values[name] = value
    for category, items in day.entries.items():
        target.entries.setdefault(category, []).extend(items)
    target.meds.extend(day.meds)
    target.weights.extend(day.weights)
    target.blood_pressures.extend(day.blood_pressures)


def _valid_date(value: str) -> bool:
    try:
        date_type.fromisoformat(value)
    except ValueError:
        return False
    return True


# --- TSV / CSV (format C) -------------------------------------------------------------------


def _header_key(name: str) -> str:
    return normalize(name)


def _column_target(key: str) -> str | None:
    return "note" if _SYMPTOMS.match(key) else _COLUMNS.get(key)


def _is_day_row(row: list[str]) -> bool:
    return bool(row) and bool(_DATE.match(row[0].strip()))


def _read_header(header: list[str], result: ParsedImport) -> list[str | None]:
    keys = [_header_key(name) for name in header]
    if any(key in _LEGACY_COLUMNS for key in keys):
        raise ImportFormatError("unsupported_format_legacy")
    targets = []
    for index, (name, key) in enumerate(zip(header, keys)):
        target = None if index == 0 else _column_target(key)
        if index > 0 and target is None and key not in _IGNORED_COLUMNS:
            result.unknown_columns.append(clean_text(name))
        targets.append(target)
    if not any(targets):
        raise ImportFormatError("missing_header")
    return targets


def _parse_table(raw_text: str, delimiter: str, result: ParsedImport) -> list[ParsedDay]:
    rows = [row for row in csv.reader(io.StringIO(raw_text.lstrip("﻿")), delimiter=delimiter)
            if any(cell.strip() for cell in row)]
    if not rows:
        raise ImportFormatError("empty_input")
    if _is_day_row(rows[0]):
        header = list(DEFAULT_HEADER)
        _issue(result, None, None, "", "default_header")
    else:
        header, rows = rows[0], rows[1:]
    targets = _read_header(header, result)

    days: list[ParsedDay] = []
    current: ParsedDay | None = None
    for row in rows:
        if _is_day_row(row):
            date = row[0].strip()
            if not _valid_date(date):
                _issue(result, date, None, date, "invalid_date")
                current = None
                continue
            current = ParsedDay(date)
            days.append(current)
        elif current is None:
            _issue(result, None, None, " | ".join(cell.strip() for cell in row if cell.strip()), "row_without_day")
            continue
        for index, cell in enumerate(row[1:], start=1):
            target = targets[index] if index < len(targets) else None
            if target and cell.strip():
                _read_cell(current, target, clean_text(header[index]), cell, result)
    return days


def _read_cell(day: ParsedDay, target: str, column: str, cell: str, result: ParsedImport) -> None:
    if target == "sleep_quality":
        _set_value(day, "sleep_quality", column, cell.strip(), SLEEP_QUALITY_MIN, SLEEP_QUALITY_MAX, result)
    elif target == "digestion":
        match = _DIGESTION.match(cell.strip())
        if not match:
            _issue(result, day.date, column, cell.strip(), "digestion_format")
            return
        values = [int(match[1]), int(match[2])]
        if not all(DIGESTION_MIN <= v <= DIGESTION_MAX for v in values):
            _issue(result, day.date, column, cell.strip(), "digestion_range")
            return
        for name, value in zip(("stool", "gas"), values):
            _store_value(day, name, column, value, result)
    elif target == "weight":
        for part in split_entries(cell):
            try:
                day.weights.append({"kg": validate_weight(part), "measured_at": None, "note": None})
            except MeasurementError as exc:
                _issue(result, day.date, column, part, exc.code)
    elif target == "blood_pressure":
        for part in split_entries(cell):
            try:
                day.blood_pressures.append({**parse_blood_pressure(part), "note": None})
            except MeasurementError as exc:
                _issue(result, day.date, column, part, exc.code)
    elif target == "note":
        text = "\n".join(line for line in (clean_text(p) for p in cell.splitlines()) if line)
        _add_items(day.entries.setdefault("note", []), [ParsedItem(text)], day.date, column, result)
    elif target == "meds":
        parts = [piece for part in split_entries(cell) for piece in (clean_text(p) for p in part.split("+")) if piece]
        _add_items(day.meds, merge_duplicates(parts), day.date, column, result)
    else:  # food categories and sport
        _add_items(day.entries.setdefault(target, []), merge_duplicates(split_entries(cell)), day.date, column, result)


def _add_items(target: list[ImportItem], items: list[ParsedItem], date: str, column: str, result: ParsedImport) -> None:
    for item in items:
        if len(item.text) > TEXT_MAX_LENGTH:
            _issue(result, date, column, item.text, "text_too_long")
        else:
            target.append(ImportItem(item.text, item.quantity, item.unit if item.quantity is not None else None))


def _set_value(day: ParsedDay, name: str, column: str, raw: str, low: int, high: int, result: ParsedImport) -> None:
    try:
        value = int(raw)
    except ValueError:
        _issue(result, day.date, column, raw, f"{name}_format")
        return
    if not low <= value <= high:
        _issue(result, day.date, column, raw, f"{name}_range")
        return
    _store_value(day, name, column, value, result)


def _store_value(day: ParsedDay, name: str, column: str, value: int, result: ParsedImport) -> None:
    """A day has one value; a different second value (another row of the day) is reported."""
    if name in day.values and day.values[name] != value:
        _issue(result, day.date, column, value, "duplicate_value")
    else:
        day.values[name] = value


# --- JSON (FoodExport) ----------------------------------------------------------------------

_VALUE_RANGES = {
    "sleep_quality": (SLEEP_QUALITY_MIN, SLEEP_QUALITY_MAX),
    "stool": (DIGESTION_MIN, DIGESTION_MAX),
    "gas": (DIGESTION_MIN, DIGESTION_MAX),
}


def _parse_json(raw_text: str, result: ParsedImport) -> list[ParsedDay]:
    try:
        export = FoodExport.model_validate_json(raw_text.lstrip("﻿"))
    except ValidationError:
        raise ImportFormatError("invalid_json") from None
    days = []
    for source in export.days:
        if not _DATE.match(source.date) or not _valid_date(source.date):
            _issue(result, source.date, None, source.date, "invalid_date")
            continue
        day = ParsedDay(source.date)
        for name in DAY_VALUE_FIELDS:
            value = getattr(source, name)
            if value is None:
                continue
            low, high = _VALUE_RANGES[name]
            if low <= value <= high:
                day.values[name] = value
            else:
                _issue(result, day.date, name, value, f"{name}_range")
        for category, entries in source.entries.items():
            if category not in ALL_CATEGORIES:
                if entries:
                    _issue(result, day.date, category, category, "unknown_category")
                continue
            items = day.entries.setdefault(category, [])
            for entry in entries:
                item = _json_entry(category, entry, day.date, result)
                if item is not None:
                    items.append(item)
        for weight in source.weights:
            try:
                day.weights.append({"kg": validate_weight(weight.kg), "measured_at": _time(weight.measured_at),
                                    "note": _note(weight.note)})
            except MeasurementError as exc:
                _issue(result, day.date, "weights", weight.kg, exc.code)
        for bp in source.blood_pressures:
            try:
                validate_blood_pressure(bp.systolic, bp.diastolic, bp.pulse)
                day.blood_pressures.append({"systolic": bp.systolic, "diastolic": bp.diastolic, "pulse": bp.pulse,
                                            "measured_at": _time(bp.measured_at), "note": _note(bp.note)})
            except MeasurementError as exc:
                _issue(result, day.date, "blood_pressures", f"{bp.systolic}/{bp.diastolic}", exc.code)
        days.append(day)
    return days


def _time(value: str | None) -> str | None:
    return normalize_time(value) if value else None


def _note(value: str | None) -> str | None:
    note = clean_text(value or "")
    if len(note) > TEXT_MAX_LENGTH:
        raise MeasurementError("note_too_long")
    return note or None


def _json_entry(category: str, entry, date: str, result: ParsedImport) -> ImportItem | None:
    is_note = CATEGORY_GROUP[category] is None
    text = ("\n".join(line for line in (clean_text(p) for p in entry.text.splitlines()) if line)
            if is_note else clean_text(entry.text))
    code = None
    if not text:
        code = "empty_text"
    elif len(text) > TEXT_MAX_LENGTH:
        code = "text_too_long"
    elif entry.quantity is not None and entry.quantity <= 0:
        code = "invalid_quantity"
    elif entry.unit and entry.unit.lower() not in UNITS:
        code = "invalid_unit"
    elif entry.intensity is not None and (
        category not in SPORT_CATEGORIES or not INTENSITY_MIN <= entry.intensity <= INTENSITY_MAX
    ):
        code = "invalid_intensity"
    if code:
        _issue(result, date, category, entry.text, code)
        return None
    try:
        quantity = None if entry.quantity is None else Decimal(str(entry.quantity)).quantize(_PRECISION)
    except InvalidOperation:
        _issue(result, date, category, entry.text, "invalid_quantity")
        return None
    unit = (entry.unit or "").lower() or None
    if unit == "ks" or quantity is None:
        unit = None
    return ImportItem(text, quantity, unit, entry.intensity)
