"""food-003 FR-4: quantity parsing from the start of the text and duplicate merging."""
from decimal import Decimal

import pytest

from app.services.food_quantity import ParsedItem, merge_duplicates, parse_quantity


def _check(raw, quantity, unit, text):
    q, u, t = parse_quantity(raw)
    assert (q, u, t) == ((Decimal(str(quantity)) if quantity is not None else None), unit, text)


def test_plain_count():
    _check("2 toasty", 2, None, "toasty")


@pytest.mark.parametrize("raw", ["2x jablko", "2× jablko", "2 x jablko"])
def test_times_sign(raw):
    _check(raw, 2, None, "jablko")


def test_fraction():
    _check("1/2 rohlika", 0.5, None, "rohlika")


@pytest.mark.parametrize("raw", [".5 l kofoly", "0,5 l kofoly", "0.5l kofoly"])
def test_decimal_litres(raw):
    _check(raw, 0.5, "l", "kofoly")


def test_decimal_litres_multiword():
    _check("0.7 l ceresnovy kompot", 0.7, "l", "ceresnovy kompot")


@pytest.mark.parametrize("raw", ["200 g ryza", "200g ryza"])
def test_grams(raw):
    _check(raw, 200, "g", "ryza")


def test_number_elsewhere_stays_in_text():
    _check("slane oplatky 20", None, None, "slane oplatky 20")


def test_number_only_is_text():
    _check("3", None, None, "3")


def test_no_number():
    _check("pho bo", None, None, "pho bo")


def test_times_with_hyphenated_text():
    _check("4x after eight - cokolada", 4, None, "after eight - cokolada")


@pytest.mark.parametrize("raw, quantity, unit, text", [
    ("2 kg jablk", 2, "kg", "jablk"),
    ("250 ml mlieka", 250, "ml", "mlieka"),
    ("3 ks vajec", 3, None, "vajec"),
    ("2 lizanky", 2, None, "lizanky"),  # "l" glued to a word is not a unit
    ("2 xylitol", 2, None, "xylitol"),
    ("0 jablk", None, None, "0 jablk"),
    ("1/0 jablka", None, None, "1/0 jablka"),
])
def test_edge_cases(raw, quantity, unit, text):
    _check(raw, quantity, unit, text)


def test_merge_duplicates_counts_repeated_items():
    merged = merge_duplicates(["emanera", "prestarium", "emanera"])
    assert [(m.text, m.quantity, m.unit) for m in merged] == [
        ("emanera", Decimal(2), None),
        ("prestarium", None, None),
    ]


def test_merge_duplicates_sums_quantities_and_ignores_case_and_diacritics():
    merged = merge_duplicates([ParsedItem("Káva", Decimal(2)), ParsedItem("kava")])
    assert [(m.text, m.quantity) for m in merged] == [("Káva", Decimal(3))]


def test_merge_duplicates_keeps_different_units_apart():
    merged = merge_duplicates(["0.5 l kofoly", "200 ml kofoly", "0,5 l kofoly"])
    assert [(m.text, m.quantity, m.unit) for m in merged] == [
        ("kofoly", Decimal("1.0"), "l"),
        ("kofoly", Decimal(200), "ml"),
    ]
