"""food-011 FR-1: parser of pasted TSV / CSV (format C) and JSON (FoodExport)."""
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.food_import_parser import ImportFormatError, detect_format, parse_import

FIXTURES = Path(__file__).parent.parent / "fixtures" / "food"
TODAY = "2026-10-24"
HEADER_C = "\t".join((
    "", "pohyb", "spanok", "Ranajky", "desiata", "obed", "olovrant", "vecera", "post vecera", "oills",
    "medical note", "presure", "dig problemy (1-10) s/v", "symptoms 12", "symptoms 2", "w", "sport ", "note",
))


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _day(parsed, date: str):
    return next(d for d in parsed.days if d.date == date)


def _items(day, category: str) -> list:
    return [(i.text, i.quantity, i.unit) for i in day.entries.get(category, [])]


def _texts(day, category: str) -> list[str]:
    return [i.text for i in day.entries.get(category, [])]


def _row(**cells) -> str:
    """The cells of one row after the date column; keys are column names with "_" for spaces."""
    columns = HEADER_C.split("\t")[1:]
    return "\t" + "\t".join(cells.get(name.strip().replace(" ", "_"), "") for name in columns)


def test_detect_format():
    assert detect_format('  {"days": []}') == "json"
    assert detect_format("a\tb\nc") == "tsv"
    assert detect_format("a,b\nc\td") == "csv"


def test_2026_tsv_day():
    parsed = parse_import(_fixture("2026.csv"), "auto", TODAY)
    assert parsed.format == "tsv"
    day = _day(parsed, "2026-10-23")
    assert _texts(day, "breakfast") == ["ryza"]
    assert _texts(day, "morning_snack") == ["banan", "bebe oplatky"]
    assert _items(day, "lunch") == [("ryza 1/2 konzzervy tuniak", None, None)]
    assert _items(day, "afternoon_snack") == [("ryza 1/2 konzzervy tuniak", None, None),
                                              ("jablko", Decimal(2), None)]
    assert _items(day, "dinner") == [("toasty", Decimal(2), None), ("zemiaky jogurt", None, None)]
    assert _texts(day, "after_dinner") == ["maly marhulovy kompot", "bebe oplatky"]
    assert [(bp["systolic"], bp["diastolic"]) for bp in day.blood_pressures] == [(125, 90)]
    assert day.values == {"stool": 6, "gas": 3}
    assert [w["kg"] for w in day.weights] == [Decimal("80.6")]
    assert _texts(day, "sport") == ["bike 30 km"]
    assert [(i.text, i.quantity) for i in day.meds] == [("emanera", Decimal(2)), ("prestarium", None)]


def test_2026_empty_day_skipped():
    parsed = parse_import(_fixture("2026.csv"), "auto", TODAY)
    assert "2026-09-21" in parsed.skipped_empty_days
    assert all(d.date != "2026-09-21" for d in parsed.days)
    assert parsed.unknown_columns == []


def test_data_sample_csv():
    parsed = parse_import(_fixture("data_sample.txt"), "auto", TODAY)
    assert parsed.format == "csv"
    day = _day(parsed, "2026-07-10")
    assert _items(day, "breakfast") == [("salamy chleba", None, None), ("sunka", None, None),
                                        ("nealko piva", Decimal(2), None)]
    assert day.values == {"stool": 4, "gas": 6}


def test_data_sample_meds_split_on_plus():
    day = _day(parse_import(_fixture("data_sample.txt"), "csv", TODAY), "2026-07-06")
    assert [i.text for i in day.meds] == ["zn", "mg", "omega", "fe", "D", "prestarium", "emanera"]
    # The misplaced "pistacie" in "medical note" stays a note (the app does not correct the sheet).
    assert _texts(day, "note") == ["pistacie"]


def test_trailing_comma_and_typos():
    raw = HEADER_C + "\n2026-10-20" + _row(Ranajky="kolac 2 perniky, ", obed="ryza 1/2 konzzervy tuniak")
    day = _day(parse_import(raw, "tsv", TODAY), "2026-10-20")
    assert _texts(day, "breakfast") == ["kolac 2 perniky"]
    assert _texts(day, "lunch") == ["ryza 1/2 konzzervy tuniak"]


def test_blood_pressure_out_of_range_is_an_issue():
    raw = HEADER_C + "\n2026-10-20" + _row(presure="145/02, 130/85", w="900")
    parsed = parse_import(raw, "tsv", TODAY)
    day = _day(parsed, "2026-10-20")
    assert [(bp["systolic"], bp["diastolic"]) for bp in day.blood_pressures] == [(130, 85)]
    assert day.weights == []
    assert {"date": "2026-10-20", "column": "presure", "value": "145/02", "code": "bp_range"} in parsed.issues
    assert {"date": "2026-10-20", "column": "w", "value": "900", "code": "weight_range"} in parsed.issues


def test_values_notes_and_bad_values():
    cells = {"spanok": "3", "dig_problemy_(1-10)_s/v": "11/2", "note": '"rano\n prujem"', "symptoms_12": "hlava"}
    raw = HEADER_C + "\n2026-10-20" + _row(**cells)
    parsed = parse_import(raw, "tsv", TODAY)
    day = _day(parsed, "2026-10-20")
    assert day.values == {"sleep_quality": 3}
    assert _texts(day, "note") == ["hlava", "rano\nprujem"]
    assert [i["code"] for i in parsed.issues] == ["digestion_range"]


def test_future_day_is_an_issue():
    raw = HEADER_C + "\n2026-10-25" + _row(Ranajky="ryza")
    parsed = parse_import(raw, "tsv", TODAY)
    assert parsed.days == []
    assert parsed.issues == [{"date": "2026-10-25", "column": None, "value": "2026-10-25", "code": "future_date"}]


def test_unknown_columns_and_header_variants():
    raw = " ,Spánok,pills,symptoms 1,kalorie\n2026-10-20,2,zn,bolest,2000\n"
    parsed = parse_import(raw, "auto", TODAY)
    day = _day(parsed, "2026-10-20")
    assert day.values == {"sleep_quality": 2}
    assert [i.text for i in day.meds] == ["zn"]
    assert _texts(day, "note") == ["bolest"]
    assert parsed.unknown_columns == ["kalorie"]


def test_rows_without_header_use_the_2026_columns():
    lines = _fixture("2026.csv").splitlines()[1:3]
    parsed = parse_import("\n".join(lines), "auto", TODAY)
    assert _texts(_day(parsed, "2026-10-23"), "breakfast") == ["ryza"]
    assert [i["code"] for i in parsed.issues] == ["default_header"]


@pytest.mark.parametrize("name", ["2025.csv", "2022.csv"])
def test_legacy_header(name):
    with pytest.raises(ImportFormatError) as exc:
        parse_import(_fixture(name), "auto", TODAY)
    assert exc.value.code == "unsupported_format_legacy"


@pytest.mark.parametrize("raw, code", [("  ", "empty_input"), ("{nope", "invalid_json"), ("a,b\n1,2", "missing_header")])
def test_unreadable_input(raw, code):
    with pytest.raises(ImportFormatError) as exc:
        parse_import(raw, "auto", TODAY)
    assert exc.value.code == code


def test_json():
    raw = """{"exported_at": "2026-10-24T18:00:00Z", "days": [
        {"date": "2026-10-23", "stool": 6, "gas": 30,
         "entries": {"breakfast": [{"text": " ryza ", "quantity": 2, "unit": "ks"}], "sport": [{"text": "bike", "intensity": 3}],
                     "dessert": [{"text": "x"}]},
         "weights": [{"kg": 80.6, "measured_at": "7:30"}], "blood_pressures": [{"systolic": 145, "diastolic": 2}]},
        {"date": "2026-10-22"}]}"""
    parsed = parse_import(raw, "auto", TODAY)
    assert [d.date for d in parsed.days] == ["2026-10-22", "2026-10-23"]  # empty JSON days are kept
    day = _day(parsed, "2026-10-23")
    assert day.values == {"stool": 6}
    assert _items(day, "breakfast") == [("ryza", Decimal(2), None)]
    assert day.entries["sport"][0].intensity == 3
    assert day.weights == [{"kg": Decimal("80.6"), "measured_at": "07:30", "note": None}]
    assert day.blood_pressures == []
    assert sorted(i["code"] for i in parsed.issues) == ["bp_range", "gas_range", "unknown_category"]
