"""food-003 FR-2 / FR-3: normalization and splitting of entry input."""
from app.services.food_text import clean_text, normalize, split_entries


def test_normalize_trims_collapses_and_strips_diacritics():
    assert normalize("  Smažený   Tuniak ") == "smazeny tuniak"


def test_normalize_diacritics_and_case():
    assert normalize("Ryža") == normalize("ryza") == "ryza"
    assert normalize("ČOKOLÁDA") == "cokolada"


def test_clean_text_trims():
    assert clean_text("chipsy ") == "chipsy"


def test_split_drops_empty_trailing_part_and_keeps_numbers():
    assert split_entries("kolac 2 perniky, ") == ["kolac 2 perniky"]


def test_split_on_comma_without_space():
    assert split_entries("kava,cola") == ["kava", "cola"]


def test_split_on_newline_and_empty_parts():
    assert split_entries("a\nb, ,c") == ["a", "b", "c"]


def test_split_keeps_decimal_comma():
    assert split_entries("0,5 l kofoly, 2,5 dl vody,3 jablka") == ["0,5 l kofoly", "2,5 dl vody", "3 jablka"]
