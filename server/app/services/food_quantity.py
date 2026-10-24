"""Quantity parsing from the start of an entry text (constitution D6) and duplicate merging (D7)."""
import re
from dataclasses import dataclass
from decimal import Decimal

from app.services.food_text import clean_text, normalize

# number: "2", "0,5", "0.5", ".5" or a fraction "1/2"; then optional "x"/"×" or a unit glued or spaced.
_QUANTITY = re.compile(
    r"""^(?P<num>\d+/\d+|\d+(?:[.,]\d+)?|[.,]\d+)
        (?:
            \s*[x×](?=\s|$)
          | \s*(?P<unit>kg|ml|ks|g|l)(?=\s|$)
          | (?=\s)
        )""",
    re.IGNORECASE | re.VERBOSE,
)


_PRECISION = Decimal("0.001")  # matches food_entries.quantity Numeric(10, 3)


def _to_decimal(num: str) -> Decimal | None:
    if "/" in num:
        a, b = num.split("/")
        if int(b) == 0:
            return None
        return (Decimal(a) / Decimal(b)).quantize(_PRECISION)
    return Decimal(num.replace(",", "."))


def parse_quantity(text: str) -> tuple[Decimal | None, str | None, str]:
    """Returns (quantity, unit, rest). Pieces ("ks" or no unit) are returned with unit None.
    If nothing but the quantity would remain, the whole input is text."""
    text = clean_text(text)
    match = _QUANTITY.match(text)
    if not match:
        return None, None, text
    rest = text[match.end():].strip()
    quantity = _to_decimal(match.group("num"))
    if not rest or quantity is None or quantity <= 0:
        return None, None, text
    unit = (match.group("unit") or "").lower() or None
    if unit == "ks":
        unit = None
    return quantity, unit, rest


@dataclass
class ParsedItem:
    text: str
    quantity: Decimal | None = None
    unit: str | None = None


def parse_item(raw: str) -> ParsedItem:
    quantity, unit, text = parse_quantity(raw)
    return ParsedItem(text, quantity, unit)


def merge_duplicates(items: list[ParsedItem | str]) -> list[ParsedItem]:
    """Items with the same normalized text and unit become one item with the summed quantity
    (a missing quantity counts as 1 piece); different units stay separate. The first occurrence
    keeps its position and spelling. Plain strings are parsed with parse_quantity first."""
    merged: list[ParsedItem] = []
    index: dict[tuple[str, str | None], ParsedItem] = {}
    for item in items:
        if isinstance(item, str):
            item = parse_item(item)
        key = (normalize(item.text), item.unit)
        target = index.get(key)
        if target is None:
            target = index[key] = ParsedItem(item.text, item.quantity, item.unit)
            merged.append(target)
            continue
        target.quantity = (target.quantity or Decimal(1)) + (item.quantity or Decimal(1))
    return merged
