"""Display helpers of the Food diary templates."""
from decimal import Decimal

from django import template
from django.utils import formats
from django.utils.dateformat import format as format_date
from django.utils.translation import get_language

register = template.Library()


def _number(value) -> str:
    """0.5 -> "0,5" (localized decimal separator), 2.0 -> "2"; no trailing zeros."""
    text = f"{Decimal(str(value)).normalize():f}"
    return text.replace(".", formats.get_format("DECIMAL_SEPARATOR"))


@register.filter
def qty(item) -> str:
    """Quantity chip label of an entry or quantity option: "2×", "0,5 l", "200 g"; "" without a quantity."""
    if item.get("quantity") is None:
        return ""
    unit = item.get("unit")
    return f"{_number(item['quantity'])} {unit}" if unit else f"{_number(item['quantity'])}×"


@register.filter
def number(value) -> str:
    return "" if value is None else _number(value)


# Date of a day by UI language (food-010 FR-2): sk/cs "24. 10. 2026", en "24 Oct 2026".
DATE_FORMATS = {"en": "j M Y"}
DEFAULT_DATE_FORMAT = "j. n. Y"


@register.filter
def food_date(value) -> str:
    if not value:
        return ""
    return format_date(value, DATE_FORMATS.get(get_language(), DEFAULT_DATE_FORMAT))


@register.filter
def bp_raw(bp) -> str:
    """Blood pressure as the quick-entry string for editing: "130/85 72 07:30"."""
    parts = [f"{bp['systolic']}/{bp['diastolic']}"]
    if bp.get("pulse"):
        parts.append(str(bp["pulse"]))
    if bp.get("measured_at"):
        parts.append(bp["measured_at"])
    return " ".join(parts)
